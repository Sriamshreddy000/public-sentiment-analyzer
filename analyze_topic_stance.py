from db import get_conn, init_db
from stance import stance_toward_target

def fetch_unlabeled_topic_comments(limit=200):
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

def save_topic_stance(comment_id, post_id, topic_label, stance_label, stance_score):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO comment_topic_stance
            (comment_id, post_id, topic_label, stance_label, stance_score)
            VALUES (?, ?, ?, ?, ?)
        """, (comment_id, post_id, topic_label, stance_label, stance_score))
        conn.commit()

def main():
    init_db()
    rows = fetch_unlabeled_topic_comments(200)

    for comment_id, post_id, body, title in rows:
        label, score = stance_toward_target(body, title)
        save_topic_stance(comment_id, post_id, title, label, score)
        print(f"{comment_id} [{title[:60]}] -> {label} ({score:.2f})")

if __name__ == "__main__":
    main()
