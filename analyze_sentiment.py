from db import get_conn, init_db
from sentiment import analyze_sentiment

def fetch_unlabeled_comments(limit=50):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT comment_id, body
            FROM comments
            WHERE sentiment_label IS NULL
            LIMIT ?
        """, (limit,)).fetchall()
    return rows

def save_sentiment(comment_id, label, score):
    with get_conn() as conn:
        conn.execute("""
            UPDATE comments
            SET sentiment_label = ?, sentiment_score = ?
            WHERE comment_id = ?
        """, (label, score, comment_id))
        conn.commit()

def main():
    init_db()
    comments = fetch_unlabeled_comments(100)

    for cid, body in comments:
        label, score = analyze_sentiment(body)
        save_sentiment(cid, label, score)
        print(f"{cid} -> {label} ({score:.2f})")

if __name__ == "__main__":
    main()