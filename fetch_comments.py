import time
from db import init_db, get_conn, upsert_comment
from sources.arctic_shift import fetch_comments
import config

def fetch_post_ids(limit: int = 10):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT post_id FROM posts
            ORDER BY fetched_utc DESC, num_comments DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [r[0] for r in rows]

def _errors_table(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS fetch_errors (post_id TEXT PRIMARY KEY, reason TEXT)")

def record_fetch_error(post_id: str, reason: str):
    """Saved so the website can say why a post has no comments."""
    with get_conn() as conn:
        _errors_table(conn)
        conn.execute("INSERT OR REPLACE INTO fetch_errors VALUES (?, ?)", (post_id, reason))
        conn.commit()

def clear_fetch_errors():
    with get_conn() as conn:
        _errors_table(conn)
        conn.execute("DELETE FROM fetch_errors")
        conn.commit()

def fetch_comments_for_post(post_id: str, max_comments=30, order: str = "top"):
    # Comments now come from Arctic Shift (Reddit blocked logged-out .json in 2026).
    try:
        comments = fetch_comments(post_id, max_comments=max_comments, order=order)
    except Exception as exc:
        print(f"{post_id}: {exc}", flush=True)
        record_fetch_error(post_id, str(exc))
        return []
    if not comments:
        record_fetch_error(post_id, "Arctic Shift has no comments for this post yet")
    return comments

def main(posts_limit: int = 10, max_comments=30, order: str = "top"):
    init_db()
    clear_fetch_errors()
    post_ids = fetch_post_ids(limit=posts_limit)
    cap = "all" if max_comments is None else max_comments
    print(f"Found {len(post_ids)} posts to fetch comments for ({cap} per post, {order} first).", flush=True)

    fetched_utc = int(time.time())
    total = 0

    for i, post_id in enumerate(post_ids, start=1):
        comments = fetch_comments_for_post(post_id, max_comments=max_comments, order=order)
        for c in comments:
            upsert_comment(c, post_id=post_id, fetched_utc=fetched_utc)

        total += len(comments)
        print(f"[{i}/{len(post_ids)}] {post_id}: saved {len(comments)} comments", flush=True)

    print(f"\nDone. Total comments saved: {total}\n", flush=True)

if __name__ == "__main__":
    main(posts_limit=config.POSTS_LIMIT, max_comments=config.COMMENTS_PER_POST,
         order=config.COMMENT_ORDER)
