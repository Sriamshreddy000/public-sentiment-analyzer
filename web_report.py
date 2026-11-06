"""Builds the topic list and topic reports as data for the website.

Reuses the query, TF-IDF and example-picking logic from topic_detail.py,
so the website and the CLI always produce the same analysis.
"""
import sqlite3
from collections import Counter, defaultdict

import topic_detail as td
from db import init_db

DB = td.DB


def list_topics(limit=40):
    init_db()
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT p.post_id, p.subreddit, p.title, p.url, p.score,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comment_count,
               e.entity_a, e.entity_b
        FROM posts p
        LEFT JOIN post_entities e ON e.post_id = p.post_id
        ORDER BY p.fetched_utc DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {
            "index": i,  # same numbering the CLI uses
            "post_id": pid,
            "subreddit": sub,
            "title": (title or "").replace("\n", " ").strip(),
            "url": url,
            "score": score,
            "comment_count": cc,
            "entities": [e for e in (a, b) if e],
            "mode": "entity" if (a and b) else "topic",
        }
        for i, (pid, sub, title, url, score, cc, a, b) in enumerate(rows, start=1)
    ]


def build_report(topic_index: int):
    init_db()
    row = td.fetch_post_by_index(topic_index)
    if not row:
        return None

    post_id, title, subreddit, url, a, b = row
    is_entity = bool(a and b)
    fetcher = td.fetch_entity_labeled_comments if is_entity else td.fetch_topic_labeled_comments
    comments, used_len = td.load_comments_with_fallback(post_id, fetcher)

    report = {
        "index": topic_index,
        "post_id": post_id,
        "title": title,
        "subreddit": subreddit,
        "url": url,
        "mode": "entity" if is_entity else "topic",
        "entities": [a, b] if is_entity else [],
        "min_len": used_len,
        "total": 0,
        "distribution": [],
        "reasons": [],
    }
    if not comments:
        return report

    counts = Counter(lab for _, lab in comments)
    total = sum(counts.values())
    report["total"] = total
    report["distribution"] = [
        {"label": lab, "count": cnt, "pct": round(cnt / total * 100, 1)}
        for lab, cnt in counts.most_common()
    ]

    buckets = defaultdict(list)
    for body, lab in comments:
        buckets[lab].append(body)

    # Same rule as the CLI: reasons for up to 3 non-neutral groups
    non_neutral = [lab for lab, _ in counts.most_common() if lab != "neutral"][:3]
    for lab in non_neutral:
        other = [t for k, v in buckets.items() if k != lab for t in v]
        report["reasons"].append({
            "label": lab,
            "keywords": td.tfidf_terms(buckets[lab], other, top_k=10),
            "examples": td.representative_comments(buckets[lab], k=3),
        })
    return report
