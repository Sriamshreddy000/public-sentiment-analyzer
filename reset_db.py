from db import get_conn, init_db

def reset_all():
    init_db()
    with get_conn() as conn:
        # clear core data
        conn.execute("DELETE FROM comments")
        conn.execute("DELETE FROM posts")

        # clear analysis data (ignore if tables don't exist yet)
        try:
            conn.execute("DELETE FROM post_entities")
        except Exception:
            pass
        try:
            conn.execute("DELETE FROM comment_entity_stance")
        except Exception:
            pass

        conn.commit()

    print("✅ Reset: cleared posts, comments, post_entities, comment_entity_stance")

if __name__ == "__main__":
    reset_all()