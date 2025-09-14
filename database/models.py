# database/models.py
import sqlite3

def init_db():
    conn = sqlite3.connect("database/attendance.db")
    cur = conn.cursor()

     # Students table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    reg_no TEXT UNIQUE NOT NULL,
    class_name TEXT,
    dept TEXT,
    password TEXT,
    face_encoding BLOB   -- ✅ valid SQLite type for embeddings
    );
    """)


    # Faculty Table
    
    cur.execute('''CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    department TEXT
    )''')


    # Attendance table
    cur.execute("""
   CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    class_name TEXT,
    subject TEXT,
    date TEXT NOT NULL,
    status TEXT DEFAULT 'Present',
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(faculty_id) REFERENCES faculty(id),
    UNIQUE(student_id, faculty_id, date)
)

    """)

    # Lessons Table
    cur.execute('''CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    date TEXT DEFAULT (DATE('now')),
    FOREIGN KEY(faculty_id) REFERENCES faculty(id)
)
''')

   



    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully!")
