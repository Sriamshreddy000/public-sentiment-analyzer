import sqlite3
conn = sqlite3.connect("reddit.db")
conn.execute("DELETE FROM comment_entity_stance")
conn.execute("DELETE FROM comment_topic_stance")
conn.commit()
print("Cleared comment_entity_stance and comment_topic_stance")
