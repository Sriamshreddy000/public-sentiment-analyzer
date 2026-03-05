import sqlite3
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer

DB = "reddit.db"

def fetch_post_by_index(topic_index: int):
    conn = sqlite3.connect(DB)
    row = conn.execute("""
        SELECT p.post_id, p.title, p.subreddit, p.url, e.entity_a, e.entity_b
        FROM posts p
        LEFT JOIN post_entities e ON e.post_id = p.post_id
        ORDER BY p.fetched_utc DESC
        LIMIT 1 OFFSET ?
    """, (topic_index - 1,)).fetchone()
    conn.close()
    return row

def fetch_labeled_comments(post_id: str, min_len: int):
    """
    Fetch labeled comments for a post with a minimum length filter.
    We'll try strict first, then fallback if needed.
    """
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT c.body, s.combined_label
        FROM comments c
        JOIN comment_entity_stance s ON s.comment_id = c.comment_id
        WHERE c.post_id = ?
          AND c.body IS NOT NULL
          AND length(c.body) >= ?
          AND lower(c.body) NOT LIKE 'users often report submissions%'
          AND lower(c.body) NOT LIKE '%i am a bot%'
    """, (post_id, min_len)).fetchall()
    conn.close()
    return rows

def tfidf_terms(texts_in_bucket, texts_other, top_k=10):
    if len(texts_in_bucket) < 2 or len(texts_other) < 2:
        return []

    corpus = texts_in_bucket + texts_other
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_df=0.9)
    X = vec.fit_transform(corpus)
    feats = vec.get_feature_names_out()

    a = X[:len(texts_in_bucket)].mean(axis=0).A1
    b = X[len(texts_in_bucket):].mean(axis=0).A1
    diff = a - b

    out = []
    for i in diff.argsort()[::-1]:
        if diff[i] <= 0:
            break
        out.append(feats[i])
        if len(out) >= top_k:
            break
    return out

def representative_comments(texts, k=3):
    texts = sorted(texts, key=len, reverse=True)
    reps = []
    for t in texts:
        t = t.replace("\n", " ").strip()
        if len(t) > 320:
            t = t[:320] + "..."
        reps.append(t)
        if len(reps) >= k:
            break
    return reps

def bar(cnt, total, width=28):
    if total <= 0:
        return ""
    filled = int(round((cnt / total) * width))
    return "█" * filled + "░" * (width - filled)

def show_topic_report(topic_index: int):
    row = fetch_post_by_index(topic_index)
    if not row:
        print("Invalid topic number (no such topic in DB).")
        return

    post_id, title, subreddit, url, a, b = row

    print("\n" + "=" * 95)
    print(f"TOPIC #{topic_index}: {title}")
    print(f"subreddit=r/{subreddit} | post_id={post_id}")
    if url:
        print(f"url={url}")
    print(f"entities = ({a}, {b})")

    # Try strict first, then fallback so it never looks “empty”
    comments = fetch_labeled_comments(post_id, min_len=40)
    used_len = 40
    if not comments:
        comments = fetch_labeled_comments(post_id, min_len=10)
        used_len = 10

    if not comments:
        print("\nNo labeled comments found for this topic yet.")
        print("Tip: Run option 2 (Refresh) to refetch + analyze.")
        return

    labels = [lab for _, lab in comments]
    counts = Counter(labels)
    total = sum(counts.values())

    print(f"\nLabeled comments used: {total}  (min comment length filter = {used_len})\n")

    # Visual distribution
    for lab, cnt in counts.most_common():
        pct = (cnt / total) * 100
        print(f"{lab:18s} {bar(cnt, total)}  {cnt:3d} ({pct:5.1f}%)")

    # Reasons only for non-neutral (cleaner + more meaningful)
    bucket_texts = defaultdict(list)
    for body, lab in comments:
        bucket_texts[lab].append(body)

    non_neutral = [lab for lab, _ in counts.most_common() if lab != "neutral"]
    print("\nReasons (non-neutral only):")
    if not non_neutral:
        print("  (All neutral — no strong leaning detected.)")
        return

    for lab in non_neutral[:3]:
        in_bucket = bucket_texts[lab]
        other = []
        for k, v in bucket_texts.items():
            if k != lab:
                other.extend(v)

        terms = tfidf_terms(in_bucket, other, top_k=10)
        reps = representative_comments(in_bucket, k=3)

        print(f"\n--- {lab} ---")
        print("keywords:", ", ".join(terms) if terms else "(not enough data)")
        print("examples:")
        for i, r in enumerate(reps, start=1):
            print(f"  {i}. {r}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python topic_detail.py <topic_number>")
        raise SystemExit(1)
    show_topic_report(int(sys.argv[1]))