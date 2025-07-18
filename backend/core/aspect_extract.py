import os
import json
import asyncio
from typing import List

async def batch_llm_extract_aspects(reviews: List[str], batch_size: int = 25, max_concurrent_batches: int = 15) -> List[dict]:
    """
    For each review, use LLM to extract all mentioned aspects/themes and the sentiment for each aspect.
    Returns a list of dicts per review: [{aspects: [{aspect, sentiment}, ...]}, ...]
    Processes batches concurrently up to max_concurrent_batches.
    """
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    client = openai.AsyncOpenAI(api_key=api_key)

    system_prompt = (
        "You are an expert product review analyst. For each review, extract all product aspects or themes mentioned (e.g., shipping, durability, price, smell, packaging, customer service, etc.) and the sentiment (positive, negative, or neutral) expressed about each aspect.\n"
        "Return your answer as a JSON list of objects, one per review. Each object should have an 'aspects' key, which is a list of objects with 'aspect' and 'sentiment' keys.\n"
        "Example output for 2 reviews:\n"
        "[\n  {\"aspects\": [{\"aspect\": \"shipping\", \"sentiment\": \"negative\"}, {\"aspect\": \"price\", \"sentiment\": \"neutral\"}]},\n    {\"aspects\": [{\"aspect\": \"durability\", \"sentiment\": \"positive\"}]}\n]"
    )

    semaphore = asyncio.Semaphore(max_concurrent_batches)
    all_results = [None] * len(reviews)

    async def process_batch(batch_idx, batch, start_idx):
        async with semaphore:
            user_prompt = "Reviews:\n" + "\n".join(f"{j+1}. {r}" for j, r in enumerate(batch))
            try:
                response = await client.chat.completions.create(
                    model="gpt-4.1-2025-04-14",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    max_tokens=3000
                )
                batch_results = json.loads(response.choices[0].message.content.strip())
                if isinstance(batch_results, list):
                    all_results[start_idx:start_idx+len(batch)] = batch_results
                else:
                    all_results[start_idx:start_idx+len(batch)] = [{} for _ in batch]
            except Exception as e:
                print(f"Error in aspect extraction batch {batch_idx+1}: {e}")
                all_results[start_idx:start_idx+len(batch)] = [{} for _ in batch]

    tasks = []
    for i in range(0, len(reviews), batch_size):
        batch = reviews[i:i+batch_size]
        batch_idx = i // batch_size
        tasks.append(process_batch(batch_idx, batch, i))
    await asyncio.gather(*tasks)
    return all_results 