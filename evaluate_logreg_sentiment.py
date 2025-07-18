import os
import pandas as pd
import numpy as np
import asyncio
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import openai
from dotenv import load_dotenv

# CONFIGURE
INPUT_CSV = "chewy_sentiment_train.csv"
TEXT_COL = "REVIEW_TEXT"
LABEL_COL = "label"
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "text-embedding-3-large"
BATCH_SIZE = 100
TEST_SIZE = 0.2  # 20% for testing

# 1. Load data
df = pd.read_csv(INPUT_CSV)
texts = df[TEXT_COL].astype(str).tolist()
labels = df[LABEL_COL].astype(str).tolist()

# 2. Encode labels
le = LabelEncoder()
y = le.fit_transform(labels)

# 3. Split data
X_train, X_test, y_train, y_test = train_test_split(texts, y, test_size=TEST_SIZE, random_state=42, stratify=y)

# 4. Async embedding function
async def embed_texts(texts, api_key, model=EMBED_MODEL, batch_size=BATCH_SIZE):
    client = openai.AsyncOpenAI(api_key=api_key)
    all_embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
        batch = texts[i:i+batch_size]
        response = await client.embeddings.create(
            model=model,
            input=batch
        )
        batch_embeds = [d.embedding for d in response.data]
        all_embeddings.extend(batch_embeds)
    return np.array(all_embeddings)

# 5. Run embedding and evaluation
async def main():
    print(f"Embedding {len(X_train)} train and {len(X_test)} test reviews...")
    X_train_emb = await embed_texts(X_train, OPENAI_API_KEY)
    X_test_emb = await embed_texts(X_test, OPENAI_API_KEY)
    print("Training logistic regression...")
    clf = LogisticRegression(max_iter=1000, multi_class='multinomial', solver='lbfgs')
    clf.fit(X_train_emb, y_train)
    print("Evaluating on test set...")
    y_pred = clf.predict(X_test_emb)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

if __name__ == "__main__":
    asyncio.run(main())