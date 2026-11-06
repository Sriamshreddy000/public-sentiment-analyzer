from nli_model import classify

# Zero-shot classifier (facebook/bart-large-mnli): works without training.
# Model loading and batching live in nli_model.py.
KINDS = ("support", "oppose", "neutral")


def _labels(target: str):
    return [
        f"supports {target}",
        f"opposes {target}",
        f"is neutral or unclear about {target}",
    ]


def stance_toward_target_batch(texts: list[str], target: str):
    """Returns [(support|oppose|neutral, score), ...] for each text."""
    return [(KINDS[i], score) for i, score in classify(texts, _labels(target))]


def stance_toward_target(text: str, target: str):
    """
    Returns one of:
      - support
      - oppose
      - neutral
    """
    if not text or not target:
        return None, None
    return stance_toward_target_batch([text], target)[0]
