from db import get_conn, init_db
from entity_stance import stance_to_entity, combine_two_entities

# For now we hardcode the 2 entities because your current dataset is worldnews.
# Later we’ll auto-detect entities from title.
ENTITY_A = "USA"
ENTITY_B = "Iran"

def fetch_unlabeled_comments(limit=50):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT c.comment_id, c.body
            FROM comments c
            LEFT JOIN comment_entity_stance s ON s.comment_id = c.comment_id
            WHERE s.comment_id IS NULL
            LIMIT ?
        """, (limit,)).fetchall()
    return rows

def save_entity_stance(comment_id, entity_a, entity_b, stance_a, score_a, stance_b, score_b, combined_label, combined_score):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO comment_entity_stance
            (comment_id, entity_a, entity_b, stance_a, score_a, stance_b, score_b, combined_label, combined_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (comment_id, entity_a, entity_b, stance_a, score_a, stance_b, score_b, combined_label, combined_score))
        conn.commit()

def main():
    init_db()
    rows = fetch_unlabeled_comments(50)

    for cid, body in rows:
        stance_a, score_a = stance_to_entity(body, ENTITY_A)
        stance_b, score_b = stance_to_entity(body, ENTITY_B)
        combined_label, combined_score = combine_two_entities(ENTITY_A, stance_a, score_a, ENTITY_B, stance_b, score_b)

        save_entity_stance(
            cid, ENTITY_A, ENTITY_B,
            stance_a, score_a,
            stance_b, score_b,
            combined_label, combined_score
        )

        print(f"{cid}: {combined_label} ({combined_score:.2f}) | USA={stance_a}({score_a:.2f}) Iran={stance_b}({score_b:.2f})")

if __name__ == "__main__":
    main()