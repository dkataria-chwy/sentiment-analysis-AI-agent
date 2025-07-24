import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Any
import random
from datetime import datetime
import re

# remember the n_samples is for sameple review per sentiment and not per keyword.
def build_stats_summary(reviews: List[Dict], top_keywords: Dict[str, List[str]], keyword_matched_samples: Dict[str, Dict[str, list]], n_samples: int = 5) -> Dict[str, Any]:
    """
    keyword_matched_samples: {sentiment: {keyword: [sample_review1, sample_review2, ...]}}
    """
    # Sentiment counts and percentages
    sentiment_labels = [r.get('sentiment') for r in reviews]
    label_map = {"0": "negative", "1": "neutral", "2": "positive", 0: "negative", 1: "neutral", 2: "positive"}
    sentiment_strs = [label_map.get(str(l), str(l)) for l in sentiment_labels]
    sentiment_counts = dict(Counter(sentiment_strs))
    total = sum(sentiment_counts.values())
    sentiment_percentages = {k: round(100*v/total, 2) for k, v in sentiment_counts.items()}

    # Star rating distribution
    star_ratings = [str(r.get('product_rating')) for r in reviews if r.get('product_rating') is not None]
    star_rating_distribution = dict(Counter(star_ratings))

    # Sample reviews by sentiment
    sample_reviews = {}
    for sentiment in ['positive', 'neutral', 'negative']:
        texts = [r.get('clean') for r in reviews if label_map.get(str(r.get('sentiment')), str(r.get('sentiment'))) == sentiment and r.get('clean')]
        if texts:
            sample_reviews[sentiment] = random.sample(texts, min(n_samples, len(texts)))
        else:
            sample_reviews[sentiment] = []

    # Sentiment confidence (average and distribution)
    sentiment_confidence = {}
    sentiment_to_idx = {'negative': '0', 'neutral': '1', 'positive': '2'}
    for sentiment in ['positive', 'neutral', 'negative']:
        idx = sentiment_to_idx[sentiment]
        probs = [r['sentiment_probabilities'].get(idx, None) for r in reviews if isinstance(r, dict) and isinstance(r.get('sentiment_probabilities'), dict)]
        probs = [float(p) for p in probs if p is not None]
        if probs:
            sentiment_confidence[sentiment] = {
                'avg': float(np.mean(probs)),
                'min': float(np.min(probs)),
                'max': float(np.max(probs)),
                'std': float(np.std(probs)),
            }
        else:
            sentiment_confidence[sentiment] = None

    # Review length stats (in words)
    review_length_stats = {}
    for sentiment in ['positive', 'neutral', 'negative']:
        lengths = [len((r.get('clean') or '').split()) for r in reviews if label_map.get(str(r.get('sentiment')), str(r.get('sentiment'))) == sentiment and r.get('clean')]
        if lengths:
            review_length_stats[sentiment] = {
                'avg': float(np.mean(lengths)),
                'min': int(np.min(lengths)),
                'max': int(np.max(lengths)),
                'median': float(np.median(lengths)),
            }
        else:
            review_length_stats[sentiment] = None

    # Time trends (if created_date available)
    time_trends = defaultdict(lambda: Counter())
    for r in reviews:
        date = r.get('created_date')
        sentiment = label_map.get(str(r.get('sentiment')), str(r.get('sentiment')))
        if date and sentiment:
            try:
                if isinstance(date, str):
                    dt = datetime.fromisoformat(date)
                else:
                    dt = date
                month = dt.strftime('%Y-%m')
                time_trends[month][sentiment] += 1
            except Exception:
                continue
    time_trends = {month: dict(counts) for month, counts in time_trends.items()}

    # Most common bigrams (optional, per sentiment)
    def get_bigrams(texts):
        bigrams = []
        for text in texts:
            tokens = re.findall(r'\w+', text.lower())
            bigrams.extend([f'{tokens[i]} {tokens[i+1]}' for i in range(len(tokens)-1)])
        return [w for w, _ in Counter(bigrams).most_common(10)]
    common_bigrams = {}
    for sentiment in ['positive', 'neutral', 'negative']:
        texts = [r.get('clean') for r in reviews if label_map.get(str(r.get('sentiment')), str(r.get('sentiment'))) == sentiment and r.get('clean')]
        common_bigrams[sentiment] = get_bigrams(texts)

    return {
        'sentiment_counts': sentiment_counts,
        'sentiment_percentages': sentiment_percentages,
        'star_rating_distribution': star_rating_distribution,
        'top_keywords': top_keywords,
        'sample_reviews': sample_reviews,
        'keyword_matched_samples': keyword_matched_samples,
        'sentiment_confidence': sentiment_confidence,
        'review_length_stats': review_length_stats,
        'time_trends': time_trends,
        'common_bigrams': common_bigrams,
    }

def aggregate_aspect_sentiment(aspect_results, cleaned_reviews, top_n=10, samples_per_aspect=3):
    """
    aspect_results: output from batch_llm_extract_aspects (list of dicts with 'aspects')
    cleaned_reviews: list of cleaned review dicts (same order as aspect_results)
    Returns: list of dicts [{aspect, positive, neutral, negative, mentions, sample_reviews: {positive: [...], neutral: [...], negative: [...]}}]
    """
    from collections import defaultdict, Counter
    aspect_counts = defaultdict(lambda: Counter())
    aspect_samples = defaultdict(lambda: {'positive': [], 'neutral': [], 'negative': []})
    for idx, result in enumerate(aspect_results):
        if not isinstance(result, dict):
            continue
        for asp in result.get('aspects', []):
            aspect = asp['aspect'].lower()
            sentiment = asp['sentiment'].lower()
            aspect_counts[aspect][sentiment] += 1
            aspect_counts[aspect]['total'] += 1
            # Collect sample reviews per sentiment
            if len(aspect_samples[aspect][sentiment]) < samples_per_aspect:
                aspect_samples[aspect][sentiment].append(cleaned_reviews[idx].get('clean', ''))
    aspect_summary = []
    for aspect, counts in aspect_counts.items():
        total = counts['total']
        aspect_summary.append({
            'aspect': aspect,
            'positive': 100 * counts['positive'] / total if total else 0,
            'neutral': 100 * counts['neutral'] / total if total else 0,
            'negative': 100 * counts['negative'] / total if total else 0,
            'mentions': total,
            'sample_reviews': aspect_samples[aspect]
        })
    aspect_summary.sort(key=lambda x: x['mentions'], reverse=True)
    return aspect_summary[:top_n] 