import sqlite3

def save_face_image(student_id, image_path):
    conn = sqlite3.connect("database/attendance.db")
    cur = conn.cursor()
    with open(image_path, "rb") as f:
        img_blob = f.read()
    cur.execute("UPDATE students SET face_encoding=? WHERE id=?", (img_blob, student_id))
    conn.commit()
    conn.close()

def load_face_images():
    conn = sqlite3.connect("database/attendance.db")
    cur = conn.cursor()
    cur.execute("SELECT id, name, face_encoding FROM students WHERE face_encoding IS NOT NULL")
    data = cur.fetchall()
    conn.close()

    students = []
    for row in data:
        student_id, name, img_blob = row
        img_path = f"temp_{student_id}.jpg"
        with open(img_path, "wb") as f:
            f.write(img_blob)
        students.append((student_id, name, img_path))
    return students






'''import sqlite3, numpy as np

def save_face_encoding(student_id, encoding):
    conn = sqlite3.connect("database/attendance.db")
    cur = conn.cursor()
    cur.execute("UPDATE students SET face_encoding=? WHERE id=?", 
                (encoding.tobytes(), student_id))
    conn.commit()
    conn.close()

def load_all_face_encodings():
    conn = sqlite3.connect("database/attendance.db")
    cur = conn.cursor()
    cur.execute("SELECT id, name, face_encoding FROM students WHERE face_encoding IS NOT NULL")
    data = cur.fetchall()
    conn.close()

    students = []
    for row in data:
        student_id, name, encoding_blob = row
        encoding = np.frombuffer(encoding_blob, dtype=np.float64)
        students.append((student_id, name, encoding))
    return students
'''