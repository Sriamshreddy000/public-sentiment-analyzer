"""Reddit data via the Arctic Shift archive (https://arctic-shift.photon-reddit.com).

Reddit blocked logged-out .json access in 2026, so we read Reddit posts and
comments from Arctic Shift instead. It returns Reddit's own field names
(id, title, subreddit, score, num_comments, permalink, body, ...), so the
existing db.upsert_post / db.upsert_comment work unchanged.

Notes:
- No API key needed. It's a free community service with no uptime guarantee,
  so we keep requests sequential and modest.
- score / num_comments are snapshots frozen ~36h after a post is created,
  so very new posts look quiet. We look back 48h and rank by num_comments.
"""
import time
from datetime import datetime

import requests

BASE_URL = "https://arctic-shift.photon-reddit.com/api"
HEADERS = {"User-Agent": "public-sentiment-analyzer/0.1 (personal research project)"}
PAGE_SIZE = 100  # API maximum per request
RETRIES = 3      # extra attempts after a failed request
RETRYABLE = {429, 500, 502, 503, 504}


def _wait_seconds(r, attempt: int) -> float:
    """How long to wait before retrying: honour the server's hint on 429, else back off 2s, 4s, 8s."""
    if r is not None and r.status_code == 429:
        for header in ("Retry-After", "X-RateLimit-Reset"):
            try:
                return min(60.0, max(1.0, float(r.headers.get(header, ""))))
            except ValueError:
                pass
    return 2.0 * (2 ** attempt)


def _get(endpoint: str, params: dict) -> list:
    reason = "unknown error"
    for attempt in range(RETRIES + 1):
        r = None
        try:
            r = requests.get(f"{BASE_URL}/{endpoint}", params=params, headers=HEADERS, timeout=60)
        except requests.Timeout:
            reason = "Arctic Shift timed out"
        except requests.RequestException as exc:
            reason = f"could not reach Arctic Shift ({type(exc).__name__})"
        else:
            if r.status_code == 200:
                body = r.json()
                if isinstance(body, dict) and body.get("error"):
                    raise RuntimeError(f"Arctic Shift said: {body['error']}")
                return body.get("data") or []
            reason = ("Arctic Shift rate limit (too many requests)" if r.status_code == 429
                      else f"Arctic Shift returned HTTP {r.status_code}")
            if r.status_code not in RETRYABLE:
                break  # e.g. 400/404: retrying won't help
        if attempt < RETRIES:
            wait = _wait_seconds(r, attempt)
            print(f"{endpoint}: {reason}; retrying in {wait:.0f}s ({attempt + 1}/{RETRIES})", flush=True)
            time.sleep(wait)
    raise RuntimeError(reason)


def _to_epoch(value):
    """created_utc may come back as a unix timestamp or an ISO string."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(float(value))
    except ValueError:
        return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp())


def _is_removed(text) -> bool:
    return text in ("[deleted]", "[removed]")


def fetch_recent_posts(subreddit: str = "worldnews", hours_back: int = 48,
                       limit: int = 40, sort: str = "trending", max_pages: int = 5) -> list[dict]:
    """sort="trending": posts from the last `hours_back` hours, most-discussed first.
    sort="newest": the most recent posts, newest first."""
    if sort == "newest":
        max_pages = 1
    start = int(time.time()) - hours_back * 3600
    before = int(time.time())
    posts = {}

    for _ in range(max_pages):  # page backwards in time until the window is covered
        batch = _get("posts/search", {
            "subreddit": subreddit, "after": start, "before": before,
            "sort": "desc", "limit": PAGE_SIZE,
        })
        if not batch:
            break
        for p in batch:
            p["created_utc"] = _to_epoch(p.get("created_utc"))
            posts[p["id"]] = p
        oldest = min(p["created_utc"] for p in batch if p["created_utc"])
        if len(batch) < PAGE_SIZE or oldest <= start:
            break
        before = oldest

    keep = [
        p for p in posts.values()
        if p.get("title")
        and not p.get("removed_by_category")
        and not _is_removed(p.get("selftext"))
    ]
    if sort == "newest":
        keep.sort(key=lambda p: p.get("created_utc") or 0, reverse=True)
    else:
        keep.sort(key=lambda p: p.get("num_comments") or 0, reverse=True)
    return keep[:limit]


def _usable(c: dict) -> bool:
    return bool(c.get("body")) and not _is_removed(c["body"])


def fetch_comments(post_id: str, max_comments: int | None = 80, order: str = "top",
                   max_pages: int = 50) -> list[dict]:
    """Comments for one post (replies included).

    max_comments=None fetches every comment (up to max_pages * 100).
    order="top": most upvoted first. This needs every comment before ranking,
    so it always pages through the whole thread.
    order="newest": newest first, and stops paging once the cap is reached.
    """
    fetch_everything = max_comments is None or order == "top"
    seen: dict[str, dict] = {}
    before = None

    for _ in range(max_pages):  # page backwards in time through the thread
        params = {"link_id": post_id, "limit": PAGE_SIZE, "sort": "desc"}
        if before:
            params["before"] = before
        rows = _get("comments/search", params)
        if not rows:
            break

        new = 0
        for c in rows:
            if not c.get("id") or c["id"] in seen:
                continue
            c["created_utc"] = _to_epoch(c.get("created_utc"))
            seen[c["id"]] = c
            new += 1

        if not fetch_everything and sum(map(_usable, seen.values())) >= max_comments:
            break
        oldest = min((c["created_utc"] for c in rows if c.get("created_utc")), default=None)
        if len(rows) < PAGE_SIZE or new == 0 or oldest is None:
            break
        before = oldest + 1  # inclusive of the oldest second; duplicates are skipped above

    comments = [c for c in seen.values() if _usable(c)]
    if order == "top":
        comments.sort(key=lambda c: c.get("score") or 0, reverse=True)
    else:
        comments.sort(key=lambda c: c.get("created_utc") or 0, reverse=True)
    return comments if max_comments is None else comments[:max_comments]
