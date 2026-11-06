from collections import defaultdict

from db import get_conn, init_db
from stance import stance_toward_target_batch

def fetch_unlabeled_topic_comments(limit=-1):  # -1 = no limit
    with get_conn() as conn:
        return conn.execute("""
            SELECT c.comment_id, c.post_id, c.body, p.title
            FROM comments c
            JOIN posts p ON p.post_id = c.post_id
            JOIN post_entities e ON e.post_id = c.post_id
            LEFT JOIN comment_topic_stance s ON s.comment_id = c.comment_id
            WHERE s.comment_id IS NULL
              AND (e.entity_b IS NULL OR trim(e.entity_b) = '')
            LIMIT ?
        """, (limit,)).fetchall()

def save_topic_stances(rows):
    with get_conn() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO comment_topic_stance
            (comment_id, post_id, topic_label, stance_label, stance_score)
            VALUES (?, ?, ?, ?, ?)
        """, rows)
        conn.commit()

def main():
    init_db()
    rows = fetch_unlabeled_topic_comments()

    by_post = defaultdict(list)
    for comment_id, post_id, body, title in rows:
        by_post[(post_id, title)].append((comment_id, body))

    total, done = len(rows), 0
    print(f"Labeling {total} comments across {len(by_post)} topics", flush=True)

    for (post_id, title), items in by_post.items():
        results = stance_toward_target_batch([body for _, body in items], title)
        save_topic_stances([
            (cid, post_id, title, label, score)
            for (cid, _), (label, score) in zip(items, results)
        ])
        done += len(items)
        print(f"Labeled {done}/{total} comments ({title[:50]})", flush=True)

if __name__ == "__main__":
    main()
