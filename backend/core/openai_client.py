import os
from openai import AsyncOpenAI
from typing import List
import json
import aiohttp
import numpy as np
import pickle
import asyncio
from .aspect_extract import batch_llm_extract_aspects
import tiktoken

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
    Automatically batches requests to avoid API limits.
    """
    # Sanitize input: remove non-string and empty string values
    input_texts = [t for t in texts if isinstance(t, str) and t.strip()]
    print(f"Embedding input sample: {input_texts[:5]}")
    print(f"Total to embed: {len(input_texts)}")
    if not input_texts:
        raise ValueError("No valid texts to embed: input is empty after filtering.")
    client = get_openai_client()
    BATCH_SIZE = 2048
    all_embeddings = []
    for i in range(0, len(input_texts), BATCH_SIZE):
        batch = input_texts[i:i+BATCH_SIZE]
        print(f"Embedding batch {i//BATCH_SIZE+1}: size {len(batch)}")
        response = await client.embeddings.create(
            model="text-embedding-3-large",
            input=batch
        )
        all_embeddings.extend([d.embedding for d in response.data])
    return all_embeddings

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

    # encoding = tiktoken.encoding_for_model("gpt-4.1-2025-04-14")
    encoding = tiktoken.get_encoding("cl100k_base")
    system_tokens = len(encoding.encode(system_prompt))
    user_tokens = len(encoding.encode(user_prompt))
    print(f"[CLEANING] System prompt tokens: {system_tokens}")
    print(f"[CLEANING] User prompt tokens: {user_tokens}")

    response = await client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=15000
    )
    output_text = response.choices[0].message.content
    output_tokens = len(encoding.encode(output_text))
    print(f"[CLEANING] Output tokens: {output_tokens}")
    print(f"[CLEANING] Total tokens: {system_tokens + user_tokens + output_tokens}")
    try:
        steps = json.loads(output_text.strip())
        if isinstance(steps, list) and all(isinstance(x, list) for x in steps):
            return steps
    except Exception:
        pass
    return [["html", "encoding", "emoji", "control", "whitespace", "langdetect"] for _ in reviews]

# Batch LLM call for aspect/theme extraction
# async def batch_llm_extract_aspects(reviews: List[str], batch_size: int = 100, max_concurrent_batches: int = 15) -> List[dict]:
#     """
#     For each review, use LLM to extract all mentioned aspects/themes and the sentiment for each aspect.
#     Returns a list of dicts per review: [{aspects: [{aspect, sentiment}, ...]}, ...]
#     Processes batches concurrently up to max_concurrent_batches.
#     """
#     import openai
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise RuntimeError("OPENAI_API_KEY not set in environment")
#     client = openai.AsyncOpenAI(api_key=api_key)
#
#     system_prompt = (
#         "You are an expert product review analyst. For each review, extract all product aspects or themes mentioned (e.g., shipping, durability, price, smell, packaging, customer service, etc.) and the sentiment (positive, negative, or neutral) expressed about each aspect.\n"
#         "Return your answer as a JSON list of objects, one per review. Each object should have an 'aspects' key, which is a list of objects with 'aspect' and 'sentiment' keys.\n"
#         "Example output for 2 reviews:\n"
#         "[\n  {\"aspects\": [{\"aspect\": \"shipping\", \"sentiment\": \"negative\"}, {\"aspect\": \"price\", \"sentiment\": \"neutral\"}]},\n    {\"aspects\": [{\"aspect\": \"durability\", \"sentiment\": \"positive\"}]}\n]"
#     )
#
#     semaphore = asyncio.Semaphore(max_concurrent_batches)
#     all_results = [None] * len(reviews)
#
#     async def process_batch(batch_idx, batch, start_idx):
#         async with semaphore:
#             user_prompt = "Reviews:\n" + "\n".join(f"{j+1}. {r}" for j, r in enumerate(batch))
#             try:
#                 response = await client.chat.completions.create(
#                     model="gpt-4.1-2025-04-14",
#                     messages=[
#                         {"role": "system", "content": system_prompt},
#                         {"role": "user", "content": user_prompt}
#                     ],
#                     temperature=0.0,
#                     max_tokens=70000
#                 )
#                 batch_results = json.loads(response.choices[0].message.content.strip())
#                 if isinstance(batch_results, list):
#                     all_results[start_idx:start_idx+len(batch)] = batch_results
#                 else:
#                     all_results[start_idx:start_idx+len(batch)] = [{} for _ in batch]
#             except Exception as e:
#                 print(f"Error in aspect extraction batch {batch_idx+1}: {e}")
#                 all_results[start_idx:start_idx+len(batch)] = [{} for _ in batch]
#
#     tasks = []
#     for i in range(0, len(reviews), batch_size):
#         batch = reviews[i:i+batch_size]
#         batch_idx = i // batch_size
#         tasks.append(process_batch(batch_idx, batch, i))
#     await asyncio.gather(*tasks)
#     return all_results 