from db import get_conn, init_db
from entity_extractor import extract_entities

# simple cleanup rules for V1
BLOCKLIST = {"ai", "god", "war", "world", "article", "monday", "wednesday"}

ALIASES = {
    "U.S.": "US",
    "U.S": "US",
    "United States": "US",
    "America": "US",
    "US Navy": "US",
    "U.S. Navy": "US",
    "Iranian": "Iran",
}

def normalize(e: str) -> str:
    e = (e or "").strip()
    return ALIASES.get(e, e)

def pick_two_entities(entities):
    # Prefer likely "actors" — geopolitics tends to be ORG/GPE not random phrases.
    # We already get GPE/ORG/PERSON from spaCy, but we filter more.

    # extra junk filters
    BAD_SUBSTRINGS = [
        "thread", "day", "part", "workers", "summons", "missing", "million", "reuters",
        "live", "update", "report", "claims", "sources", "officials"
    ]

    cleaned = []
    for e in entities:
        e2 = normalize(e)
        if not e2:
            continue

        low = e2.lower()

        if low in BLOCKLIST:
            continue

        # remove super long “entities”
        if len(e2) > 25:
            continue

        # remove junky entities
        if any(b in low for b in BAD_SUBSTRINGS):
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

def fetch_posts(limit=40):
    with get_conn() as conn:
        return conn.execute("""
            SELECT post_id, title
            FROM posts
            ORDER BY fetched_utc DESC
            LIMIT ?
        """, (limit,)).fetchall()

def ensure_post_entities_table():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS post_entities (
                post_id TEXT PRIMARY KEY,
                entity_a TEXT,
                entity_b TEXT
            )
        """)
        conn.commit()

def save_post_entities(post_id, a, b):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO post_entities (post_id, entity_a, entity_b)
            VALUES (?, ?, ?)
        """, (post_id, a, b))
        conn.commit()

def main():
    init_db()
    ensure_post_entities_table()

    posts = fetch_posts(40)
    print(f"Scanning {len(posts)} posts for entities...\n")

    for post_id, title in posts:
        ents = extract_entities(title)
        a, b = pick_two_entities(ents)
        save_post_entities(post_id, a, b)
        print(f"{post_id}: {title[:80]}... -> {a}, {b}")

if __name__ == "__main__":
    main()