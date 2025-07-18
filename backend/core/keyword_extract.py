from keybert import KeyBERT
from typing import List, Dict

def extract_top_keywords_by_sentiment(reviews: List[Dict], top_n: int = 20) -> Dict[str, List[str]]:
    """
    For each sentiment (positive, neutral, negative), extract top N keywords from cleaned review texts using KeyBERT.
    reviews: list of dicts with at least 'clean' and 'sentiment' keys
    Returns: {sentiment: [keywords]}
    """
    sentiment_groups = {"positive": [], "neutral": [], "negative": []}
    label_map = {"0": "negative", "1": "neutral", "2": "positive"}
    for review in reviews:
        label = review.get("sentiment")
        label_str = label_map.get(str(label), str(label))
        if label_str in sentiment_groups:
            text = review.get("clean") or ""
            if text.strip():
                sentiment_groups[label_str].append(text)
    kw_model = KeyBERT()
    top_keywords = {}
    for sentiment, texts in sentiment_groups.items():
        if texts:
            joined = ". ".join(texts)
            keywords = kw_model.extract_keywords(joined, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=top_n)
            top_keywords[sentiment] = [kw for kw, _ in keywords]
        else:
            top_keywords[sentiment] = []
    return top_keywords 