import sqlite3

conn = sqlite3.connect('summaries.db')
cursor = conn.cursor()

# Check for DS3 content specifically
cursor.execute("SELECT * FROM summaries WHERE content_type LIKE '%ds3%'")
ds3_results = cursor.fetchall()
print(f"DS3-related entries: {len(ds3_results)}")
if ds3_results:
    for row in ds3_results:
        print(f"\n=== DS3 Page {row[1]} Analysis ===")
        print(f"Content Type: {row[2]}")
        print(f"Summary length: {len(row[3])}")
        print(f"Full summary:\n{row[3]}")
        print("-" * 80)

conn.close()
