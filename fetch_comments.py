import time
import requests
from db import init_db, get_conn, upsert_comment

HEADERS = {"User-Agent": "reddit-sentiment-learning-script/0.1"}

def fetch_post_ids(limit: int = 10):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT post_id FROM posts
            ORDER BY fetched_utc DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [r[0] for r in rows]

def fetch_comments_for_post(post_id: str, max_comments: int = 30):
    url = f"https://www.reddit.com/comments/{post_id}.json"
    r = requests.get(url, headers=HEADERS, timeout=20)

    # If Reddit blocks, it may return HTML instead of JSON
    ct = (r.headers.get("content-type") or "").lower()
    if r.status_code != 200:
        print(f"{post_id}: HTTP {r.status_code}")
        return []
    if "application/json" not in ct:
        print(f"{post_id}: not JSON (content-type={ct}). First 120 chars: {r.text[:120]!r}")
        return []

    data = r.json()

    # data = [post_listing, comments_listing]
    if not isinstance(data, list) or len(data) < 2:
        print(f"{post_id}: unexpected JSON shape")
        return []

    children = data[1].get("data", {}).get("children", [])
    comments = []

    for item in children:
        # "t1" = comment, "more" = placeholder, etc.
        if item.get("kind") != "t1":
            continue

        c = item.get("data", {})
        body = c.get("body")
        if not body or body in ("[deleted]", "[removed]"):
            continue

        comments.append(c)
        if len(comments) >= max_comments:
            break

    return comments

def main(posts_limit: int = 10, max_comments: int = 30):
    init_db()
    post_ids = fetch_post_ids(limit=posts_limit)
    print(f"Found {len(post_ids)} posts to fetch comments for.")

    fetched_utc = int(time.time())
    total = 0

    for post_id in post_ids:
        comments = fetch_comments_for_post(post_id, max_comments=max_comments)
        for c in comments:
            upsert_comment(c, post_id=post_id, fetched_utc=fetched_utc)

        total += len(comments)
        print(f"{post_id}: saved {len(comments)} comments")

    print(f"\nDone. Total comments saved: {total}\n")

if __name__ == "__main__":
    main(posts_limit=25, max_comments=80)