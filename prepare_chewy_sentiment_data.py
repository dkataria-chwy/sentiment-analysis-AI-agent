import pandas as pd

# CONFIGURE THESE
INPUT_CSV = "chewy_reviews_raw.csv"      # Your input file (replace with your filename)
OUTPUT_CSV = "chewy_sentiment_train.csv" # Output file for training
TEXT_COL = "REVIEW_TEXT"                 # Name of the text column in your CSV
RATING_COL = "RATING"                    # Name of the rating column in your CSV

# 1. Load data
df = pd.read_csv(INPUT_CSV)

# 2. Drop rows with missing/blank review text
df = df.dropna(subset=[TEXT_COL])
df = df[df[TEXT_COL].str.strip() != ""]

# 3. Map ratings to sentiment labels
def map_rating_to_label(rating):
    try:
        r = int(rating)
        if r <= 2:
            return "negative"
        elif r == 3:
            return "neutral"
        elif r >= 4:
            return "positive"
    except Exception:
        return None

df["label"] = df[RATING_COL].apply(map_rating_to_label)

# 4. Drop rows with unmapped labels (e.g., missing/invalid ratings)
df = df.dropna(subset=["label"])

# 5. (Optional) Remove duplicates
df = df.drop_duplicates(subset=[TEXT_COL, "label"])

# 6. Save to new CSV (keep RATING column)
df[[TEXT_COL, RATING_COL, "label"]].to_csv(OUTPUT_CSV, index=False)
print(f"Saved {len(df)} labeled reviews to {OUTPUT_CSV}")