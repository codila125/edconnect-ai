import sqlite3

conn = sqlite3.connect('summaries.db')
cursor = conn.cursor()

# Delete existing page 12 entries
cursor.execute("DELETE FROM summaries WHERE page=12")
deleted_count = cursor.rowcount

print(f"Deleted {deleted_count} entries for page 12")

conn.commit()
conn.close()
