"""Pipeline settings. Edit the defaults here for the CLI.

The website's Refresh controls override them for a single run
(the server passes them to the pipeline scripts as PSA_* environment variables).
"""
import os


def _int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(os.getenv(name, default))))
    except ValueError:
        return default


SUBREDDIT = os.getenv("PSA_SUBREDDIT", "worldnews")

# How many topics (posts) to fetch and analyze
POSTS_LIMIT = _int("PSA_POSTS", 15, 1, 50)

# "trending" = most-discussed posts from the last HOURS_BACK hours
# "newest"   = most recent posts (these will have fewer comments so far)
SORT = os.getenv("PSA_SORT", "trending")
if SORT not in ("trending", "newest"):
    SORT = "trending"

HOURS_BACK = _int("PSA_HOURS_BACK", 48, 1, 168)

# Comments analyzed per post: a number, or "all" for every comment the post has.
# Every one goes through the BART model (twice for entity-vs-entity topics),
# so this drives refresh time. "all" on busy posts can take a long while.
_raw_comments = os.getenv("PSA_COMMENTS", "30").strip().lower()
COMMENTS_PER_POST = None if _raw_comments == "all" else _int("PSA_COMMENTS", 30, 5, 5000)

# Which comments to keep when capped: "top" (most upvoted) or "newest".
# Note: Arctic Shift scores are snapshots taken ~36h after posting,
# so scores on very recent comments are close to 0.
COMMENT_ORDER = os.getenv("PSA_COMMENT_ORDER", "top")
if COMMENT_ORDER not in ("top", "newest"):
    COMMENT_ORDER = "top"
