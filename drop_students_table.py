import sqlite3

conn = sqlite3.connect("database/attendance.db")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS students")
conn.commit()
conn.close()

print("✅ Dropped old students table")
