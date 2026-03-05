from transformers import pipeline

clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def stance_to_entity(text: str, entity: str):
    """
    Returns: ('support'|'oppose'|'neutral', score)
    """
    labels = [
        f"supports {entity}",
        f"opposes {entity}",
        f"is neutral or unclear about {entity}"
    ]
    res = clf(text[:512], labels, multi_label=False)
    best = res["labels"][0]
    score = float(res["scores"][0])

    if best.startswith("supports"):
        return "support", score
    if best.startswith("opposes"):
        return "oppose", score
    return "neutral", score

def combine_two_entities(entity_a, stance_a, score_a, entity_b, stance_b, score_b, thresh=0.60):
    # Direct support labels
    if stance_a == "support" and score_a >= thresh:
        return f"pro-{entity_a}", score_a
    if stance_b == "support" and score_b >= thresh:
        return f"pro-{entity_b}", score_b

    # Direct oppose labels
    if stance_a == "oppose" and score_a >= thresh:
        return f"anti-{entity_a}", score_a
    if stance_b == "oppose" and score_b >= thresh:
        return f"anti-{entity_b}", score_b

    return "neutral", max(score_a, score_b)