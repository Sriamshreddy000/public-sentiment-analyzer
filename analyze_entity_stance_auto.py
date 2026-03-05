from db import get_conn, init_db
from entity_stance import stance_to_entity, combine_two_entities

def fetch_unlabeled(limit=80):
    with get_conn() as conn:
        return conn.execute("""
            SELECT c.comment_id, c.body, c.post_id, e.entity_a, e.entity_b
            FROM comments c
            JOIN post_entities e ON e.post_id = c.post_id
            LEFT JOIN comment_entity_stance s ON s.comment_id = c.comment_id
            WHERE s.comment_id IS NULL
            LIMIT ?
        """, (limit,)).fetchall()

def save_entity_stance(comment_id, entity_a, entity_b,
                       stance_a, score_a, stance_b, score_b,
                       combined_label, combined_score):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO comment_entity_stance
            (comment_id, entity_a, entity_b, stance_a, score_a, stance_b, score_b, combined_label, combined_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (comment_id, entity_a, entity_b, stance_a, score_a, stance_b, score_b, combined_label, combined_score))
        conn.commit()

def main():
    init_db()
    rows = fetch_unlabeled(200)

    for cid, body, post_id, a, b in rows:
        if not a or not b:
            # if only one entity, treat as neutral for now (next step will handle single-topic stance)
            continue

        stance_a, score_a = stance_to_entity(body, a)
        stance_b, score_b = stance_to_entity(body, b)

        combined_label, combined_score = combine_two_entities(a, stance_a, score_a, b, stance_b, score_b)

        save_entity_stance(cid, a, b, stance_a, score_a, stance_b, score_b, combined_label, combined_score)
        print(f"{cid} [{a} vs {b}] -> {combined_label} ({combined_score:.2f})")

if __name__ == "__main__":
    main()