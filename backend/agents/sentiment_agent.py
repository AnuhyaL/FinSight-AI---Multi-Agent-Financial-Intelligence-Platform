from collections import Counter


def analyze_sentiment(texts: list[str]) -> dict:
    """Use FinBERT when installed; deterministic lexical fallback keeps API available."""
    labels: list[dict] = []
    try:
        from transformers import pipeline
        classifier = pipeline("text-classification", model="ProsusAI/finbert")
        labels = [{"label": item["label"].lower(), "confidence": item["score"]} for item in classifier(texts)]
    except (ImportError, OSError, RuntimeError):
        positive = {"growth", "beat", "strong", "upside", "profit", "positive"}
        negative = {"risk", "decline", "loss", "lawsuit", "weak", "negative"}
        for text in texts:
            words = set(text.lower().split())
            label = "positive" if len(words & positive) > len(words & negative) else "negative" if words & negative else "neutral"
            labels.append({"label": label, "confidence": 0.55})
    majority = Counter(item["label"] for item in labels).most_common(1)[0][0]
    return {"sentiment": majority, "confidence": round(sum(x["confidence"] for x in labels) / len(labels), 3), "items": labels}
