import sqlite3
import datetime

DB_PATH = "database/attendance.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Fetch student & faculty IDs
cur.execute("SELECT id, reg_no FROM students")
students = cur.fetchall()

cur.execute("SELECT id, name FROM faculty")
faculties = cur.fetchall()

# Attendance for 10 days
base_date = datetime.date.today()

attendance_records = []

# Arjun (100%) → all Present
for i in range(10):
    attendance_records.append((students[0][0], faculties[0][0], "III-A", "Maths", str(base_date - datetime.timedelta(days=i)), "Present"))

# Priya (60%) → 6 Present, 4 Absent
for i in range(6):
    attendance_records.append((students[1][0], faculties[0][0], "III-A", "Maths", str(base_date - datetime.timedelta(days=i)), "Present"))
for i in range(6, 10):
    attendance_records.append((students[1][0], faculties[0][0], "III-A", "Maths", str(base_date - datetime.timedelta(days=i)), "Absent"))

# Rahul (50%) → 5 Present, 5 Absent
for i in range(5):
    attendance_records.append((students[2][0], faculties[1][0], "III-B", "DBMS", str(base_date - datetime.timedelta(days=i)), "Present"))
for i in range(5, 10):
    attendance_records.append((students[2][0], faculties[1][0], "III-B", "DBMS", str(base_date - datetime.timedelta(days=i)), "Absent"))

# Kavya (80%) → 8 Present, 2 Absent
for i in range(8):
    attendance_records.append((students[3][0], faculties[2][0], "II-A", "Networks", str(base_date - datetime.timedelta(days=i)), "Present"))
for i in range(8, 10):
    attendance_records.append((students[3][0], faculties[2][0], "II-A", "Networks", str(base_date - datetime.timedelta(days=i)), "Absent"))

# Manoj (40%) → 4 Present, 6 Absent
for i in range(4):
    attendance_records.append((students[4][0], faculties[0][0], "IV-A", "Robotics", str(base_date - datetime.timedelta(days=i)), "Present"))
for i in range(4, 10):
    attendance_records.append((students[4][0], faculties[0][0], "IV-A", "Robotics", str(base_date - datetime.timedelta(days=i)), "Absent"))

# Insert dummy attendance
cur.executemany("""
    INSERT OR IGNORE INTO attendance (student_id, faculty_id, class_name, subject, date, status)
    VALUES (?, ?, ?, ?, ?, ?)
""", attendance_records)

conn.commit()
conn.close()

print("✅ Dummy attendance inserted. Some students now have <75% attendance for testing.")
