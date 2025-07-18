import os
import pandas as pd
import numpy as np
import asyncio
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

import openai
from dotenv import load_dotenv

# CONFIGURE
INPUT_CSV = "chewy_sentiment_train.csv"
TEXT_COL = "REVIEW_TEXT"
LABEL_COL = "label"
MODEL_PATH = "backend/models/logreg_sentiment.pkl"
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it before running the script.")
EMBED_MODEL = "text-embedding-3-large"
BATCH_SIZE = 100

# 1. Load data
df = pd.read_csv(INPUT_CSV)
texts = df[TEXT_COL].astype(str).tolist()
labels = df[LABEL_COL].astype(str).tolist()

# 2. Encode labels
le = LabelEncoder()
y = le.fit_transform(labels)

# 3. Async embedding function
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

# 4. Run embedding
async def main():
    print(f"Embedding {len(texts)} reviews...")
    embeddings = await embed_texts(texts, OPENAI_API_KEY)
    print("Training logistic regression...")
    clf = LogisticRegression(max_iter=1000, multi_class='multinomial', solver='lbfgs')
    clf.fit(embeddings, y)
    # Save model and label encoder
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    with open(MODEL_PATH.replace('.pkl', '_label_encoder.pkl'), "wb") as f:
        pickle.dump(le, f)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    asyncio.run(main())