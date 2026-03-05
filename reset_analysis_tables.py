import sqlite3

conn = sqlite3.connect("reddit.db")

conn.execute("DELETE FROM comments")
conn.execute("DELETE FROM comment_stance")
conn.execute("DELETE FROM comment_entity_stance")

conn.commit()
conn.close()

print("Cleared comments + stance tables.")