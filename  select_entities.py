# simple cleanup rules for V1
BLOCKLIST = {"ai", "god", "war", "world", "article", "monday", "wednesday"}

ALIASES = {
    "U.S.": "US",
    "U.S": "US",
    "United States": "US",
    "America": "US",
    "Iranian": "Iran",
}

def normalize(e: str) -> str:
    e = (e or "").strip()
    if e in ALIASES:
        e = ALIASES[e]
    return e

def pick_two_entities(entities):
    # normalize + filter
    cleaned = []
    for e in entities:
        e2 = normalize(e)
        if not e2:
            continue
        if e2.lower() in BLOCKLIST:
            continue
        cleaned.append(e2)

    # dedupe preserve order
    deduped = []
    seen = set()
    for e in cleaned:
        k = e.lower()
        if k in seen:
            continue
        seen.add(k)
        deduped.append(e)

    if len(deduped) >= 2:
        return deduped[0], deduped[1]
    if len(deduped) == 1:
        return deduped[0], None
    return None, None