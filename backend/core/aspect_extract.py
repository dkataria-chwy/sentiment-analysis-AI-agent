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

    system_prompt = """You are an expert product sentiment analyst specializing in customer reviews. Your task is to extract ALL product aspects and themes mentioned in reviews and analyze sentiment with high precision and consistency.

ASPECT EXTRACTION GUIDELINES:
1. **Comprehensive Aspect Extraction**: Extract ANY product aspect or theme mentioned in the review, including but not limited to:
   - Physical properties such as: size, weight, texture, durability, material, color, shape
   - Performance aspects such as: effectiveness, functionality, ease of use, value for money
   - Pet-related aspects (when applicable) such as: pet enjoyment, pet interest, appeal to pets, safety for pets
   - User experience aspects such as: packaging, shipping, customer service, instructions
   - Sensory aspects such as: smell, taste, sound, appearance
   - Any other themes, features, or characteristics mentioned by reviewers

2. **Consistency Rules**:
   - Use standardized aspect names (e.g., always "pet_interest" not "dog interest" or "cat appeal")
   - Group similar concepts under one aspect (e.g., "pet_enjoyment" covers "dog likes it", "cat loves it")
   - Be specific but not overly granular (e.g., "texture" not "rough texture" + "smooth texture")

3. **Sentiment Analysis Rules**:
   - **Positive**: Clear positive language, satisfaction, recommendation, exceeded expectations
   - **Negative**: Clear negative language, dissatisfaction, problems, unmet expectations  
   - **Neutral**: Factual statements, mixed feelings, conditional opinions, questions
   - Consider context and intensity (e.g., "somewhat disappointed" vs "absolutely terrible")

4. **Complex Language Handling** (including but not limited to these patterns):
   - Handle negations carefully: "not bad" ≠ negative sentiment
   - Identify sarcasm: "Oh great, another broken toy" = negative about durability
   - Separate comparative statements: "better than expected" = positive
   - Extract implied aspects: "arrived quickly" implies shipping aspect
   - Recognize any other complex language patterns, irony, understatement, or nuanced expressions

5. **Multi-aspect Sentences** (extract all aspects mentioned, including but not limited to):
   - Split when different sentiments: "Good quality but too expensive" → durability:positive, price:negative
   - Extract all mentioned aspects even if sentiment unclear
   - Handle compound statements, lists of features, or any other multi-faceted comments
   - Identify any themes or aspects mentioned regardless of sentence complexity

STANDARDIZED ASPECT NAMES (these are examples only - extract ANY aspect or theme mentioned):
- Common examples include but are not limited to: durability, size, weight, texture, material, color, appearance
- Pet-related examples include but are not limited to: pet_interest, pet_enjoyment, pet_safety, chew_appeal  
- Sensory examples include but are not limited to: smell, taste, sound
- Experience examples include but are not limited to: price, value, shipping, packaging, customer_service
- Performance examples include but are not limited to: ease_of_use, effectiveness, quality, design
- Extract and name ANY other aspects, themes, features, or characteristics mentioned using clear, descriptive terms
- Do not limit yourself to these examples - identify ALL aspects present in reviews regardless of category

OUTPUT FORMAT:
Return a JSON list with one object per review. Each object has:
- "aspects": list of {"aspect": "standardized_name", "sentiment": "positive/negative/neutral"}

Example output for 2 reviews:
[
  {"aspects": [{"aspect": "shipping", "sentiment": "negative"}, {"aspect": "price", "sentiment": "neutral"}]},
  {"aspects": [{"aspect": "durability", "sentiment": "positive"}]}
]

QUALITY CHECKS:
- Extract ALL aspects mentioned in the review, not just common ones
- Don't extract aspects not actually mentioned
- Don't assume sentiment from irrelevant context
- Use clear, descriptive aspect names even for unusual or unique features mentioned"""

    semaphore = asyncio.Semaphore(max_concurrent_batches)
    all_results = [None] * len(reviews)

    async def process_batch(batch_idx, batch, start_idx):
        async with semaphore:
            # Create more structured user prompt
            user_prompt = f"""Analyze the following {len(batch)} product reviews for aspects and sentiment:
                REVIEWS:
                """ + "\n".join(f"Review {j+1}: {r}" for j, r in enumerate(batch)) + """

                Extract aspects and sentiment for each review following the guidelines above. Focus on consistency and accuracy."""
            try:
                response = await client.chat.completions.create(
                    model="gpt-4.1-2025-04-14",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=3000
                )
                content = response.choices[0].message.content.strip()
                # Handle potential wrapper objects
                if content.startswith('{"reviews":'):
                    batch_results = json.loads(content)["reviews"]
                else:
                    batch_results = json.loads(content)
                    
                if isinstance(batch_results, list):
                    all_results[start_idx:start_idx+len(batch)] = batch_results
                else:
                    all_results[start_idx:start_idx+len(batch)] = [{}] * len(batch)
                    
            except Exception as e:
                print(f"Error in aspect extraction batch {batch_idx+1}: {e}")
                all_results[start_idx:start_idx+len(batch)] = [{}] * len(batch)

    tasks = []
    for i in range(0, len(reviews), batch_size):
        batch = reviews[i:i+batch_size]
        batch_idx = i // batch_size
        tasks.append(process_batch(batch_idx, batch, i))
    
    await asyncio.gather(*tasks)
    return all_results


