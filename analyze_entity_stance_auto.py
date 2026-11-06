from collections import defaultdict

from db import get_conn, init_db
from entity_stance import stance_to_entity_batch, combine_two_entities

def fetch_unlabeled(limit=-1):  # -1 = no limit
    with get_conn() as conn:
        return conn.execute("""
            SELECT c.comment_id, c.body, c.post_id, e.entity_a, e.entity_b
            FROM comments c
            JOIN post_entities e ON e.post_id = c.post_id
            LEFT JOIN comment_entity_stance s ON s.comment_id = c.comment_id
            WHERE s.comment_id IS NULL
              AND e.entity_a IS NOT NULL
              AND e.entity_b IS NOT NULL
            LIMIT ?
        """, (limit,)).fetchall()

def save_entity_stances(rows):
    with get_conn() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO comment_entity_stance
            (comment_id, entity_a, entity_b, stance_a, score_a, stance_b, score_b, combined_label, combined_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()

def main():
    init_db()
    rows = fetch_unlabeled()

    # Group by topic so each entity's comments go through the model as one batch
    by_topic = defaultdict(list)
    for cid, body, post_id, a, b in rows:
        by_topic[(post_id, a, b)].append((cid, body))

    total, done = len(rows), 0
    print(f"Labeling {total} comments across {len(by_topic)} entity topics", flush=True)

    for (post_id, a, b), items in by_topic.items():
        texts = [body for _, body in items]
        res_a = stance_to_entity_batch(texts, a)
        res_b = stance_to_entity_batch(texts, b)

        out = []
        for (cid, _), (stance_a, score_a), (stance_b, score_b) in zip(items, res_a, res_b):
            label, score = combine_two_entities(a, stance_a, score_a, b, stance_b, score_b)
            out.append((cid, a, b, stance_a, score_a, stance_b, score_b, label, score))
        save_entity_stances(out)  # saved per topic, so progress isn't lost if a later one fails

        done += len(items)
        print(f"Labeled {done}/{total} comments ({a} vs {b})", flush=True)

if __name__ == "__main__":
    main()
