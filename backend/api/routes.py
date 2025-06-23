from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict
import uuid
from core.fetch_reviews import fetch_reviews
from core.clean_text import CleanTextPipeline
import pandas as pd
import os
from core.clean_text_graph import clean_reviews_langgraph
from dotenv import load_dotenv
import asyncio
import json
from core.openai_client import embed_texts, classify_embeddings
from core.keyword_extract import extract_top_keywords_by_sentiment
from core.stats_build import build_stats_summary
import re
import string
import numpy as np
from core.gpt_summary import generate_gpt_summary

load_dotenv()

router = APIRouter()

# In-memory job store for demo (replace with Redis/DB in prod)
jobs: Dict[str, dict] = {}

# Flag to toggle between LLM+LangGraph and classic CleanTextPipeline
USE_LLM_CLEAN = os.getenv("USE_LLM_CLEAN", "false").lower() == "true"
import logging
logging.info(f"USE_LLM_CLEAN (from env): {USE_LLM_CLEAN}")

def save_step_output(step_num, data):
    with open(f"step_{step_num}.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

@router.post("/analyze/{sku}")
async def analyze_sku(sku: str):
    print(f"analyze_sku called for SKU: {sku}")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "result": None, "reviews": None, "step": 0}
    asyncio.create_task(run_analysis_async(sku, job_id))
    return {"job_id": job_id}

async def run_analysis_async(sku: str, job_id: str):
    print(f"run_analysis_async called for SKU: {sku}, job_id: {job_id}")
    logging.info(f"run_analysis_async called for SKU: {sku}, job_id: {job_id}")
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["step"] = 0  # FetchReviews
    jobs[job_id]["cleantext_substeps"] = {
        "html": "pending",
        "encoding": "pending",
        "emoji": "pending",
        "control": "pending",
        "whitespace": "pending"
    }
    reviews = []
    for review in fetch_reviews(sku):
        reviews.append(review)
        if len(reviews) >= 5000:
            break
    jobs[job_id]["reviews"] = reviews
    save_step_output(1, reviews)
    logging.info(f"Fetched {len(reviews)} reviews. Starting null/dup filter.")
    # --- Null, blank, and duplicate filter ---
    df = pd.DataFrame(reviews)
    before = len(df)
    df = df.dropna(subset=["customer_review"])
    df = df[df["customer_review"].str.strip() != ""]
    df = df.drop_duplicates(subset=["customer_review"])
    filtered_reviews = df.to_dict(orient="records")
    after = len(filtered_reviews)
    save_step_output(2, filtered_reviews)
    logging.info(f"Filtered reviews: {before} -> {after} after null/blank/dup filter.")
    logging.info(f"Starting CleanText step.")
    jobs[job_id]["step"] = 1  # CleanText
    # Set all sub-steps to in_progress at start of CleanText
    for sub in ["html", "encoding", "emoji", "control", "whitespace"]:
        jobs[job_id]["cleantext_substeps"][sub] = "in_progress"
    cleaned_reviews = []
    if USE_LLM_CLEAN:
        logging.info("Using LLM+LangGraph cleaning pipeline.")
        texts = [r.get("customer_review") or "" for r in filtered_reviews]
        cleaned_batch = await clean_reviews_langgraph(texts)
        for review, cleaned in zip(filtered_reviews, cleaned_batch):
            cleaned_reviews.append({**review, **cleaned})
    else:
        logging.info("Using classic CleanTextPipeline.")
        clean_pipeline = CleanTextPipeline()
        for idx, review in enumerate(filtered_reviews):
            raw_text = review.get("customer_review") or ""
            cleaned = clean_pipeline.clean(raw_text)
            cleaned_reviews.append({**review, **cleaned})
            if idx < 3:
                logging.info(f"Cleaned review {idx+1}: {cleaned}")
    # Set all sub-steps to done when CleanText completes
    for sub in ["html", "encoding", "emoji", "control", "whitespace"]:
        jobs[job_id]["cleantext_substeps"][sub] = "done"
    await asyncio.sleep(2)  # Delay to allow frontend to show 'done' state
    jobs[job_id]["cleaned_reviews"] = cleaned_reviews
    save_step_output(3, cleaned_reviews)
    logging.info(f"Completed CleanText step. {len(cleaned_reviews)} reviews cleaned.")

    # --- EmbedBatch & ClassifyBatch ---
    jobs[job_id]["step"] = 2  # EmbedBatch
    texts_to_embed = [r.get("clean") or "" for r in cleaned_reviews]
    # Only embed non-empty cleaned reviews
    valid_indices = [i for i, t in enumerate(texts_to_embed) if t.strip()]
    valid_texts = [texts_to_embed[i] for i in valid_indices]
    embeddings = []
    if valid_texts:
        embeddings = await embed_texts(valid_texts)
    else:
        logging.warning("No valid cleaned reviews to embed.")
    # Map embeddings back to original indices
    full_embeddings = [None] * len(texts_to_embed)
    for idx, emb in zip(valid_indices, embeddings):
        full_embeddings[idx] = emb
    save_step_output(4, full_embeddings)
    logging.info(f"Completed embedding for {len(valid_texts)} reviews.")

    jobs[job_id]["step"] = 3  # ClassifyBatch
    classification_results = []
    if embeddings:
        classification_results = classify_embeddings(embeddings)
    else:
        logging.warning("No embeddings to classify.")
    # Map classification results back to original indices
    full_classification = [None] * len(texts_to_embed)
    for idx, res in zip(valid_indices, classification_results):
        full_classification[idx] = res
    save_step_output(5, full_classification)
    logging.info(f"Completed classification for {len(classification_results)} reviews.")

    # Optionally, merge classification results into cleaned_reviews for downstream steps
    for i, review in enumerate(cleaned_reviews):
        review["embedding"] = full_embeddings[i]
        review["sentiment"] = full_classification[i]["label"] if full_classification[i] else None
        review["sentiment_probabilities"] = full_classification[i]["probabilities"] if full_classification[i] else None
    jobs[job_id]["classified_reviews"] = cleaned_reviews

    # --- KeywordExtract ---
    jobs[job_id]["step"] = 4  # KeywordExtract
    top_keywords = extract_top_keywords_by_sentiment(cleaned_reviews, top_n=15)
    save_step_output(6, top_keywords)
    jobs[job_id]["top_keywords"] = top_keywords
    logging.info(f"Extracted top keywords for each sentiment.")

    # --- Keyword-Matched Sample Reviews (Flexible Matching) ---
    # Map integer sentiment labels (including NumPy types) to string labels for matching
    sentiment_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
    for review in cleaned_reviews:
        val = review.get('sentiment')
        if isinstance(val, (int, float)) or (hasattr(val, 'item') and callable(val.item)):
            try:
                int_val = int(val)
                review['sentiment'] = sentiment_map.get(int_val, str(int_val))
            except Exception:
                review['sentiment'] = str(val)
    unique_sentiments = set(r.get("sentiment") for r in cleaned_reviews)
    logging.info(f"Unique sentiment labels in cleaned_reviews: {unique_sentiments}")
    def normalize(text):
        return re.sub(rf'[{re.escape(string.punctuation)}]', '', text.lower())

    keyword_matched_samples = {sentiment: {} for sentiment in top_keywords}
    for sentiment, keywords in top_keywords.items():
        sentiment_reviews = [r.get("clean") for r in cleaned_reviews if r.get("sentiment") == sentiment and r.get("clean")]
        norm_reviews = [normalize(r) for r in sentiment_reviews]
        logging.info(f"Sentiment '{sentiment}': {len(sentiment_reviews)} reviews to check.")
        for kw in keywords:
            kw_words = normalize(kw).split()
            logging.info(f"Checking keyword '{kw}' (words: {kw_words}) for sentiment '{sentiment}'...")
            # Try to find a review containing all words in the keyword
            found = False
            for review, norm_review in zip(sentiment_reviews, norm_reviews):
                if all(word in norm_review for word in kw_words):
                    keyword_matched_samples[sentiment][kw] = review
                    logging.info(f"  Found ALL match for '{kw}': {review}")
                    found = True
                    break
            # Fallback: find a review containing any word in the keyword
            if not found:
                for review, norm_review in zip(sentiment_reviews, norm_reviews):
                    if any(word in norm_review for word in kw_words):
                        keyword_matched_samples[sentiment][kw] = review
                        logging.info(f"  Found ANY match for '{kw}': {review}")
                        found = True
                        break
            if not found:
                logging.info(f"  No match found for '{kw}' in sentiment '{sentiment}'.")
    save_step_output(6.1, keyword_matched_samples)
    jobs[job_id]["keyword_matched_samples"] = keyword_matched_samples
    logging.info(f"Saved keyword-matched sample reviews for each sentiment (flexible matching).")

    # --- StatsBuild ---
    jobs[job_id]["step"] = 5  # StatsBuild
    stats_summary = build_stats_summary(cleaned_reviews, top_keywords, keyword_matched_samples, n_samples=3)
    save_step_output(7, stats_summary)
    jobs[job_id]["stats_summary"] = stats_summary
    logging.info(f"Built stats summary for dashboard and summary step.")

    await asyncio.sleep(4)
    jobs[job_id]["step"] = 6  # GptSummary
    await asyncio.sleep(4)
    jobs[job_id]["status"] = "complete"
    jobs[job_id]["result"] = {"summary": f"Fetched {len(reviews)} reviews for SKU {sku}"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    resp = {"status": job["status"], "step": job.get("step", 0)}
    if job.get("step", 0) == 1 and "cleantext_substeps" in job:
        resp["cleantext_substeps"] = job["cleantext_substeps"]
    return resp

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    job = jobs.get(job_id)
    if not job or job["status"] != "complete":
        raise HTTPException(status_code=404, detail="Results not available")
    return job["result"]

@router.get("/summary/{job_id}")
async def get_summary(job_id: str, request: Request):
    job = jobs.get(job_id)
    if not job or "stats_summary" not in job:
        raise HTTPException(status_code=404, detail="Stats summary not available for this job.")
    stats_summary = job["stats_summary"]
    summary = await generate_gpt_summary(stats_summary)
    if summary.startswith("[ERROR]"):
        raise HTTPException(status_code=500, detail=summary)
    return {
        "summary": summary,
        "stats": stats_summary
    } 