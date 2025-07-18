import regex as re
import hashlib
import pandas as pd
from bs4 import BeautifulSoup
import ftfy
import emoji
import langdetect
from spellchecker import SpellChecker
import nltk
#from nltk.corpus import stopwords  # Remove stopwords usage
from nltk.stem import WordNetLemmatizer

# Download NLTK data if not already present
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
# Remove stopwords download and usage

class CleanTextPipeline:
    def __init__(self, language='en'):
        self.spell = SpellChecker(language=language)
        # self.stopwords = set(stopwords.words(language))  # Remove stopwords usage
        self.lemmatizer = WordNetLemmatizer()

    def clean(self, text: str) -> dict:
        original = text
        # 1. Null/blank/dup filter (handled at DataFrame level)
        # 2. HTML sanitise
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
        # 3. Encoding/mojibake fix
        text = ftfy.fix_text(text)
        # 4. Emoji & control-char strip
        text = emoji.replace_emoji(text, replace="")
        text = re.sub(r"\p{C}+", " ", text)
        # 5. Whitespace normalise
        text = re.sub(r"\s+", " ", text).strip()
        # 6. Language detection
        try:
            lang = langdetect.detect(text)
        except Exception:
            lang = 'unknown'
        if lang != 'en':
            return {"clean": None, "lang": lang, "hash": self.hash_text(original)}
        # 7. Length bucketing (handled at pipeline level)
        # 8. Profanity/PII masking (optional, not implemented here)
        # 9. Hash original
        hash_val = self.hash_text(original)
        # --- Extra steps ---
        # Spell correction
        words = text.split()
        corrected = [self.spell.correction(w) if w not in self.spell else w for w in words]
        corrected = [c if c is not None else w for c, w in zip(corrected, words)]
        text = " ".join(corrected)
        # Stopword removal (removed)
        # filtered = [w for w in text.split() if w.lower() not in self.stopwords]
        # text = " ".join(filtered)
        # Lemmatization
        lemmatized = [self.lemmatizer.lemmatize(w) for w in text.split()]
        text = " ".join(lemmatized)
        return {"clean": text, "lang": lang, "hash": hash_val}

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest() 