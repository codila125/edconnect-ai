import sqlite3

conn = sqlite3.connect('summaries.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM summaries WHERE page=12")
results = cursor.fetchall()

if results:
    for row in results:
        print(f"ID: {row[0]}, Page: {row[1]}, Type: {row[2]}")
        print(f"Summary length: {len(row[3])}")
        print(f"Full summary:\n{row[3]}")
        print("-" * 80)
else:
    print("No page 12 results found")
    
# Check all pages
cursor.execute("SELECT DISTINCT page FROM summaries ORDER BY page")
pages = cursor.fetchall()
print(f"Pages in database: {[p[0] for p in pages]}")

# Look for manpower content
cursor.execute("SELECT * FROM summaries WHERE summary LIKE '%manpower%' OR summary LIKE '%Manpower%'")
manpower_results = cursor.fetchall()
print(f"\nManpower-related entries: {len(manpower_results)}")
for row in manpower_results:
    print(f"Page {row[1]}: {row[3][:200]}...")

conn.close()
