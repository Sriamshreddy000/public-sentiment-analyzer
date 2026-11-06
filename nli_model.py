"""Shared zero-shot model (facebook/bart-large-mnli) used for stance.

Same model as before, but:
- runs on the Mac's GPU (Apple MPS) when available, otherwise CPU
- classifies comments in batches instead of one at a time
"""
import os

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")  # unsupported ops fall back to CPU

from functools import lru_cache

MODEL = "facebook/bart-large-mnli"
BATCH_SIZE = int(os.getenv("PSA_BATCH_SIZE", "16"))


def _best_device():
    import torch
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return 0
    return -1  # CPU


@lru_cache(maxsize=1)
def get_classifier():
    from transformers import pipeline
    device = _best_device()
    try:
        clf = pipeline("zero-shot-classification", model=MODEL, device=device)
    except Exception as exc:  # noqa: BLE001
        print(f"Could not load model on {device} ({exc}); using CPU", flush=True)
        clf = pipeline("zero-shot-classification", model=MODEL, device=-1)
    print(f"Stance model running on: {clf.device}", flush=True)
    return clf


def classify(texts: list[str], labels: list[str]) -> list[tuple[int, float]]:
    """For each text: (index of the best label, its score)."""
    if not texts:
        return []
    clf = get_classifier()
    inputs = [(t or " ")[:512] for t in texts]
    results = clf(inputs, labels, multi_label=False, batch_size=BATCH_SIZE)
    if isinstance(results, dict):
        results = [results]
    return [(labels.index(r["labels"][0]), float(r["scores"][0])) for r in results]
