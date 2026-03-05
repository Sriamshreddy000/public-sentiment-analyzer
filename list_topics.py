from db import get_conn, init_db

def list_topics(limit=20):
    init_db()
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.post_id, p.subreddit, p.title,
                   (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comment_count
            FROM posts p
            ORDER BY p.fetched_utc DESC
            LIMIT ?
        """, (limit,)).fetchall()

    if not rows:
        print("No posts in DB. Use option 2 to refresh trending topics.")
        return

    print(f"\nShowing {len(rows)} topics:\n")
    for i, (pid, sub, title, cc) in enumerate(rows, start=1):
        title = (title or "").replace("\n", " ").strip()
        print(f"{i:2d}. r/{sub:<15}  comments={cc:<4}  id={pid}  {title[:90]}")

if __name__ == "__main__":
    list_topics()