from nli_model import classify

KINDS = ("support", "oppose", "neutral")


def _labels(entity: str):
    return [
        f"supports {entity}",
        f"opposes {entity}",
        f"is neutral or unclear about {entity}",
    ]


def stance_to_entity_batch(texts: list[str], entity: str):
    """Returns [('support'|'oppose'|'neutral', score), ...] for each text."""
    return [(KINDS[i], score) for i, score in classify(texts, _labels(entity))]


def stance_to_entity(text: str, entity: str):
    """
    Returns: ('support'|'oppose'|'neutral', score)
    """
    return stance_to_entity_batch([text], entity)[0]


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
