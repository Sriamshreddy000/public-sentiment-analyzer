import sqlite3
from pathlib import Path

DB_PATH = Path("reddit.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            subreddit TEXT NOT NULL,
            score INTEGER,
            num_comments INTEGER,
            url TEXT,
            created_utc INTEGER,
            fetched_utc INTEGER
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            comment_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            body TEXT NOT NULL,
            score INTEGER,
            author TEXT,
            created_utc INTEGER,
            fetched_utc INTEGER,

            sentiment_label TEXT,
            sentiment_score REAL,

            stance_label TEXT,
            stance_score REAL,

            FOREIGN KEY(post_id) REFERENCES posts(post_id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_sentiment (
            comment_id TEXT PRIMARY KEY,
            sentiment_label TEXT,
            sentiment_score REAL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_stance (
            comment_id TEXT PRIMARY KEY,
            stance_label TEXT,
            stance_score REAL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_entity_stance (
            comment_id TEXT PRIMARY KEY,
            entity_a TEXT,
            entity_b TEXT,
            stance_a TEXT,
            score_a REAL,
            stance_b TEXT,
            score_b REAL,
            combined_label TEXT,
            combined_score REAL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_topic_stance (
            comment_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            topic_label TEXT,
            stance_label TEXT,
            stance_score REAL,
            FOREIGN KEY(post_id) REFERENCES posts(post_id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS post_entities (
            post_id TEXT PRIMARY KEY,
            entity_a TEXT,
            entity_b TEXT
        )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")
        conn.commit()

def upsert_post(post: dict, fetched_utc: int):
    with get_conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO posts
        (post_id, title, subreddit, score, num_comments, url, created_utc, fetched_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post.get("id"),
            (post.get("title") or "").strip(),
            post.get("subreddit"),
            post.get("score"),
            post.get("num_comments"),
            "https://www.reddit.com" + post.get("permalink", ""),
            int(post.get("created_utc")) if post.get("created_utc") else None,
            fetched_utc
        ))
        conn.commit()

def upsert_comment(comment: dict, post_id: str, fetched_utc: int):
    body = comment.get("body")
    if not body or body in ("[deleted]", "[removed]"):
        return

    with get_conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO comments
        (comment_id, post_id, body, score, author, created_utc, fetched_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            comment.get("id"),
            post_id,
            body,
            comment.get("score"),
            str(comment.get("author")) if comment.get("author") is not None else None,
            int(comment.get("created_utc")) if comment.get("created_utc") else None,
            fetched_utc
        ))
        conn.commit()
