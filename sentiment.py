from transformers import pipeline

# CardiffNLP Twitter RoBERTa sentiment labels:
# LABEL_0 = negative, LABEL_1 = neutral, LABEL_2 = positive
LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
}

sentiment_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment"
)

def analyze_sentiment(text: str):
    if not text:
        return None, None

    # keep it short to avoid slowdowns
    result = sentiment_model(text[:512])[0]
    raw_label = result["label"]
    score = float(result["score"])

    label = LABEL_MAP.get(raw_label, raw_label)
    return label, score