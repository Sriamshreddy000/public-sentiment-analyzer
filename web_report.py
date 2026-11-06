"""Builds the topic list and topic reports as data for the website.

Reuses the query, TF-IDF and example-picking logic from topic_detail.py,
so the website and the CLI always produce the same analysis.
"""
import json
import sqlite3
from collections import Counter, defaultdict

import topic_detail as td
from db import init_db

DB = td.DB


def _fetch_errors(conn) -> dict:
    conn.execute("CREATE TABLE IF NOT EXISTS fetch_errors (post_id TEXT PRIMARY KEY, reason TEXT)")
    return dict(conn.execute("SELECT post_id, reason FROM fetch_errors").fetchall())


def list_topics(limit=50):
    init_db()
    conn = sqlite3.connect(DB)
    errors = _fetch_errors(conn)
    rows = conn.execute("""
        SELECT p.post_id, p.subreddit, p.title, p.url, p.score, p.num_comments,
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
            "num_comments": nc,
            "comment_count": cc,
            "fetch_error": errors.get(pid) if not cc else None,
            "entities": [e for e in (a, b) if e],
            "mode": "entity" if (a and b) else "topic",
        }
        for i, (pid, sub, title, url, score, nc, cc, a, b) in enumerate(rows, start=1)
    ]


def build_report(topic_index: int):
    init_db()
    row = td.fetch_post_by_index(topic_index)
    if not row:
        return None

    post_id, title, subreddit, url, a, b = row
    conn = sqlite3.connect(DB)
    nc, cc = conn.execute("""
        SELECT p.num_comments, (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id)
        FROM posts p WHERE p.post_id = ?
    """, (post_id,)).fetchone()
    fetch_error = _fetch_errors(conn).get(post_id) if not cc else None
    conn.close()
    is_entity = bool(a and b)
    fetcher = td.fetch_entity_labeled_comments if is_entity else td.fetch_topic_labeled_comments
    comments, used_len = td.load_comments_with_fallback(post_id, fetcher)

    report = {
        "index": topic_index,
        "post_id": post_id,
        "title": title,
        "subreddit": subreddit,
        "url": url,
        "num_comments": nc,
        "comment_count": cc,
        "excluded": 0,
        "fetch_error": fetch_error,
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
    report["excluded"] = max(0, cc - total)  # fetched but too short (or unlabeled)
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


# ---------- which settings produced the current data ----------

def _meta_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS refresh_meta (
        id INTEGER PRIMARY KEY CHECK (id = 1), options TEXT, finished_utc INTEGER)""")


def save_refresh_options(options: dict, finished_utc: int):
    conn = sqlite3.connect(DB)
    _meta_table(conn)
    conn.execute("INSERT OR REPLACE INTO refresh_meta VALUES (1, ?, ?)",
                 (json.dumps(options), finished_utc))
    conn.commit()
    conn.close()


def data_summary():
    init_db()
    conn = sqlite3.connect(DB)
    _meta_table(conn)
    topics, fetched = conn.execute("SELECT COUNT(*), MAX(fetched_utc) FROM posts").fetchone()
    comments = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    meta = conn.execute("SELECT options, finished_utc FROM refresh_meta WHERE id = 1").fetchone()
    conn.close()
    # Only trust the saved settings if no newer fetch (e.g. from the CLI) replaced the data
    options = json.loads(meta[0]) if meta and fetched and meta[1] >= fetched else None
    return {"topics": topics, "comments": comments, "fetched_utc": fetched,
            "options": options if topics else None}
