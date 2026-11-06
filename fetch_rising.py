import time
from db import init_db, upsert_post
from sources.arctic_shift import fetch_recent_posts
import config

def fetch_rising(subreddit: str = "popular", limit: int = 15, sort: str = "trending"):
    # Reddit blocked logged-out .json in 2026, so posts now come from Arctic Shift:
    # the most-discussed posts from the last 48h instead of Reddit's "rising" list.
    items = fetch_recent_posts(subreddit=subreddit, limit=limit, sort=sort,
                               hours_back=config.HOURS_BACK)

    fetched_utc = int(time.time())
    saved = 0

    print(f"\nFetched {len(items)} {sort} posts from r/{subreddit} (via Arctic Shift):\n")

    for i, p in enumerate(items, start=1):
        upsert_post(p, fetched_utc)
        saved += 1

        title = (p.get("title") or "").replace("\n", " ").strip()
        print(f"{i}. {title[:140]}")
        print(f"   id={p.get('id')}  subreddit=r/{p.get('subreddit')}  score={p.get('score')}  comments={p.get('num_comments')}")
        print(f"   url=https://www.reddit.com{p.get('permalink')}\n")

    print(f"Saved {saved} posts into reddit.db\n")

if __name__ == "__main__":
    init_db()
    fetch_rising(subreddit=config.SUBREDDIT, limit=config.POSTS_LIMIT, sort=config.SORT)
