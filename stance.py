from transformers import pipeline

# Zero-shot classifier: works without training
# (Heavier model; later we can optimize)
clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def stance_toward_target(text: str, target: str):
    """
    Returns one of:
      - support
      - oppose
      - neutral
    """
    if not text or not target:
        return None, None

    # Hypotheses we want to test
    labels = [
        f"supports {target}",
        f"opposes {target}",
        f"is neutral or unclear about {target}"
    ]

    result = clf(text[:512], labels, multi_label=False)

    best_label = result["labels"][0]
    best_score = float(result["scores"][0])

    if best_label.startswith("supports"):
        return "support", best_score
    if best_label.startswith("opposes"):
        return "oppose", best_score
    return "neutral", best_score