import os
from openai import AsyncOpenAI
from typing import List
import json
import aiohttp
import numpy as np
import pickle

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    return AsyncOpenAI(api_key=api_key)

# Embedding
async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Call OpenAI embedding API (text-embedding-3-small) for a batch of texts.
    Returns a list of 1536-D float vectors.
    """
    client = get_openai_client()
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    # The API returns a list of dicts with 'embedding' key
    return [d.embedding for d in response.data]

# Classification

def classify_embeddings(embeddings: List[List[float]]):
    """
    Load logistic regression model and predict sentiment for each embedding.
    Returns a list of dicts: {label, probabilities}
    """
    model_path = os.path.join(os.path.dirname(__file__), '../models/logreg_sentiment.pkl')
    with open(model_path, 'rb') as f:
        clf = pickle.load(f)
    X = np.array(embeddings)
    probs = clf.predict_proba(X)
    labels = clf.classes_[np.argmax(probs, axis=1)]
    results = []
    for i in range(len(embeddings)):
        results.append({
            'label': labels[i],
            'probabilities': {str(cls): float(prob) for cls, prob in zip(clf.classes_, probs[i])}
        })
    return results

# # GPT summary
# async def gpt_summary(prompt: str) -> str:
#     # TODO: Call OpenAI GPT-4.1 API
#     return "Executive summary stub."

# Batch LLM call for cleaning step selection
async def get_cleaning_steps_batch(reviews: List[str]) -> List[List[str]]:
    """
    For each review, use GPT-4.1 to decide which cleaning steps to apply.
    Returns a list of lists of step names (e.g., [ ["html", "emoji"], ... ])
    """
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    client = openai.AsyncOpenAI(api_key=api_key)

    system_prompt = (
        "You are a text cleaning expert. For each review, decide which cleaning steps are needed from the following list:\n"
        "- html: Remove HTML tags and convert to plain text.\n"
        "- encoding: Fix encoding issues and mojibake.\n"
        "- emoji: Remove emojis.\n"
        "- control: Remove control characters (e.g., invisible Unicode).\n"
        "- whitespace: Normalize whitespace (collapse spaces, trim).\n"
        "- langdetect: Detect language.\n"
        "- profanity: Mask or remove profane words.\n"
        "- pii: Mask or remove personally identifiable information (PII).\n"
        "some reviews may contain information on autoship, and you should not remove that information. Autoship is the process of automatically renewing a subscription to a product. do not spell correct the word autoship. \n"
        "Some reviews may be very long; handle them efficiently and only apply necessary steps.\n"
        "Do not invent steps not in the list. For each review, return a list of step names (in order) to apply. Output a JSON list of lists, one per review.\n"
        "Example output for 3 reviews:\n"
        "[\n  [\"html\", \"encoding\", \"emoji\", \"whitespace\"],\n  [\"langdetect\", \"profanity\"],\n  [\"html\", \"pii\", \"whitespace\"]\n]"
    )
    user_prompt = "Reviews:\n" + "\n".join(f"{i+1}. {r}" for i, r in enumerate(reviews))
    response = await client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=15000
    )
    try:
        steps = json.loads(response.choices[0].message.content.strip())
        if isinstance(steps, list) and all(isinstance(x, list) for x in steps):
            return steps
    except Exception:
        pass
    return [["html", "encoding", "emoji", "control", "whitespace", "langdetect"] for _ in reviews] 