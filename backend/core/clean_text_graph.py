import regex as re
import hashlib
from typing import List, Dict
from bs4 import BeautifulSoup
import ftfy
import emoji
import langdetect
from spellchecker import SpellChecker
from nltk.stem import WordNetLemmatizer
from core.openai_client import get_cleaning_steps_batch
import langgraph
import logging
import asyncio
from asyncio import Semaphore

# Individual cleaning step functions

def html_step(text):
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)

def encoding_step(text):
    return ftfy.fix_text(text)

def emoji_step(text):
    return emoji.replace_emoji(text, replace="")

def control_step(text):
    return re.sub(r"\\p{C}+", " ", text)

def whitespace_step(text):
    return re.sub(r"\s+", " ", text).strip()

def langdetect_step(text):
    try:
        print("LANGDETECT INPUT:", text)
        lang = langdetect.detect(text)
        print("LANGDETECT OUTPUT:", lang)
    except Exception:
        lang = 'unknown'
    return lang

def spell_step(text, spell):
    words = text.split()
    corrected = [spell.correction(w) if w not in spell else w for w in words]
    corrected = [c if c is not None else w for c, w in zip(corrected, words)]
    return " ".join(corrected)

def lemmatize_step(text, lemmatizer):
    lemmatized = [lemmatizer.lemmatize(w) for w in text.split()]
    return " ".join(lemmatized)

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# Main batch cleaning function using LangGraph

async def clean_reviews_langgraph(reviews: List[str], batch_size: int = 100, max_concurrent_batches: int = 15) -> List[Dict]:
    """
    Clean a batch of reviews using LLM-driven step selection and LangGraph orchestration.
    Splits reviews into batches to avoid context window errors. Returns a list of dicts with cleaned text, lang, and hash.
    Processes batches concurrently up to max_concurrent_batches.
    """
    spell = SpellChecker(language='en')
    lemmatizer = WordNetLemmatizer()
    cleaned = [None] * len(reviews)
    semaphore = Semaphore(max_concurrent_batches)

    async def process_batch(i):
        async with semaphore:
            batch = reviews[i:i+batch_size]
            step_lists = await get_cleaning_steps_batch(batch)
            batch_cleaned = []
            for j, text in enumerate(batch):
                original = text
                steps = step_lists[j] if j < len(step_lists) else []
                lang = 'en'  # Assume all reviews are English
                for step in steps:
                    if step == "html":
                        text = html_step(text)
                    elif step == "encoding":
                        text = encoding_step(text)
                    elif step == "emoji":
                        text = emoji_step(text)
                    elif step == "control":
                        text = control_step(text)
                    elif step == "whitespace":
                        text = whitespace_step(text)
                text = spell_step(text, spell)
                text = lemmatize_step(text, lemmatizer)
                batch_cleaned.append({"clean": text, "lang": lang, "hash": hash_text(original)})
            logging.info(f"Processed batch {(i//batch_size) + 1} ({min(i+batch_size, len(reviews))}/{len(reviews)}) reviews.")
            cleaned[i:i+batch_size] = batch_cleaned

    tasks = [process_batch(i) for i in range(0, len(reviews), batch_size)]
    await asyncio.gather(*tasks)
    return cleaned 