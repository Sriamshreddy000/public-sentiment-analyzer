import time
import requests
from db import init_db, upsert_post

def fetch_rising(subreddit: str = "popular", limit: int = 15):
    url = f"https://www.reddit.com/r/{subreddit}/rising.json"
    headers = {"User-Agent": "reddit-sentiment-learning-script/0.1"}
    params = {"limit": limit}

    r = requests.get(url, headers=headers, params=params, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    items = data["data"]["children"]

    fetched_utc = int(time.time())
    saved = 0

    print(f"\nFetched {len(items)} items from r/{subreddit} rising:\n")

    for i, item in enumerate(items, start=1):
        p = item.get("data", {})
        if not p.get("id") or not p.get("title"):
            continue

        upsert_post(p, fetched_utc)
        saved += 1

        title = (p.get("title") or "").replace("\n", " ").strip()
        print(f"{i}. {title[:140]}")
        print(f"   id={p.get('id')}  subreddit=r/{p.get('subreddit')}  score={p.get('score')}  comments={p.get('num_comments')}")
        print(f"   url=https://www.reddit.com{p.get('permalink')}\n")

    print(f"Saved {saved} posts into reddit.db\n")

if __name__ == "__main__":
    init_db()
    fetch_rising(subreddit="worldnews", limit=40)