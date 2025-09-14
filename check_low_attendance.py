import sqlite3

DB_PATH = "database/attendance.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

query = """
SELECT s.name, s.reg_no,
       SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS attendance_percentage
FROM students s
JOIN attendance a ON s.id = a.student_id
GROUP BY s.id
HAVING attendance_percentage < 75;
"""

cur.execute(query)
rows = cur.fetchall()

print("🚨 Students with <75% Attendance 🚨")
for row in rows:
    print(f"{row[0]} ({row[1]}) → {row[2]:.2f}%")

conn.close()
