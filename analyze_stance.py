from db import get_conn, init_db
from stance import stance_toward_target

def fetch_comments_with_post_titles(limit=50):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT c.comment_id, c.body, p.title
            FROM comments c
            JOIN posts p ON p.post_id = c.post_id
            LEFT JOIN comment_stance s ON s.comment_id = c.comment_id
            WHERE s.comment_id IS NULL
            LIMIT ?
        """, (limit,)).fetchall()
    return rows

def save_stance(comment_id, label, score):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO comment_stance
            (comment_id, stance_label, stance_score)
            VALUES (?, ?, ?)
        """, (comment_id, label, score))
        conn.commit()

def main():
    init_db()
    rows = fetch_comments_with_post_titles(50)

    for cid, body, title in rows:
        label, score = stance_toward_target(body, title)
        save_stance(cid, label, score)
        print(f"{cid} -> {label} ({score:.2f}) | target='{title[:60]}...'")

if __name__ == "__main__":
    main()