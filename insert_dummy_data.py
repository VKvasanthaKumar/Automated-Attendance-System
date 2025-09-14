import sqlite3
import datetime

DB_PATH = "database/attendance.db"

# Dummy student data
dummy_students = [
    ("Arjun", "21EC001", "ECE", "III-A", "arjun123"),
    ("Priya", "21EC002", "ECE", "III-A", "priya123"),
    ("Rahul", "21EC003", "CSE", "III-B", "rahul123"),
    ("Kavya", "21EC004", "IT", "II-A", "kavya123"),
    ("Manoj", "21EC005", "MECH", "IV-A", "manoj123")
]

# Dummy faculty data
dummy_faculty = [
    ("Dr. A. Kumar", "akumar@example.com", "password123", "ECE"),
    ("Prof. B. Sharma", "bsharma@example.com", "password456", "CSE"),
    ("Dr. C. Mehta", "cmehta@example.com", "password789", "EEE"),
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Insert dummy students
for name, reg_no, dept, class_name, password in dummy_students:
    cur.execute("""
        INSERT OR IGNORE INTO students (name, reg_no, dept, class_name, password)
        VALUES (?, ?, ?, ?, ?)
    """, (name, reg_no, dept, class_name, password))

# Insert dummy faculty
for name, email, password, department in dummy_faculty:
    cur.execute("""
        INSERT OR IGNORE INTO faculty (name, email, password, department) VALUES (?, ?, ?, ?)
    """, (name, email, password, department))

# Commit before attendance insert
conn.commit()

# Fetch IDs for attendance
cur.execute("SELECT id, reg_no FROM students")
students = cur.fetchall()

cur.execute("SELECT id, name FROM faculty")
faculties = cur.fetchall()

# Dummy attendance (today’s date)
today = datetime.date.today().strftime("%Y-%m-%d")

attendance_dummy = [
    (students[0][0], faculties[0][0], "III-A", "Maths", today, "Present"),
    (students[1][0], faculties[0][0], "III-A", "Maths", today, "Absent"),
    (students[2][0], faculties[1][0], "III-B", "DBMS", today, "Present"),
    (students[3][0], faculties[2][0], "II-A", "Networks", today, "Present"),
    (students[4][0], faculties[0][0], "IV-A", "Robotics", today, "Absent"),
]

cur.executemany("""
    INSERT OR IGNORE INTO attendance (student_id, faculty_id, class_name, subject, date, status)
    VALUES (?, ?, ?, ?, ?, ?)
""", attendance_dummy)

conn.commit()
conn.close()

print("✅ Dummy students, faculty, and attendance data inserted for testing!")
