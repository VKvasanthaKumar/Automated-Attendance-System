import cv2
import os
import sqlite3
from database.models import init_db
from database.helpers import save_face_image   # NEW

DB_PATH = "database/attendance.db"


def add_student_db(name, reg_no, class_name, dept, manual_password=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Insert student without password first
    cur.execute("INSERT OR IGNORE INTO students (name, reg_no, class_name, dept) VALUES (?, ?, ?, ?)",
                (name, reg_no, class_name, dept))
    conn.commit()

    # Get the student ID
    cur.execute("SELECT id FROM students WHERE reg_no=?", (reg_no,))
    student_id = cur.fetchone()[0]

    # Generate password if not provided
    password = manual_password if manual_password else f"{name}{student_id}"

    # Update password in DB
    cur.execute("UPDATE students SET password=? WHERE id=?", (password, student_id))
    conn.commit()
    conn.close()

    print(f"✅ Student enrolled with password: {password}")
    return student_id  # return ID for face saving


def capture_student_photos(name, reg_no, dept, class_name, password, max_photos=100):
    cam = cv2.VideoCapture(0)

    # Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    folder = f"dataset/{reg_no}_{name}"
    os.makedirs(folder, exist_ok=True)

    # Save student in DB and get ID
    student_id = add_student_db(name, reg_no, class_name, dept, password)

    count = 0
    capturing = False  # Start only when user presses "s"
    first_face_path = None  # To save one face in DB

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Draw rectangle around detected face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            if capturing and count < max_photos:
                file_path = os.path.join(folder, f"{count}.jpg")
                face_img = frame[y:y+h, x:x+w]  # crop face only
                cv2.imwrite(file_path, face_img)

                # Save first captured face to DB
                if first_face_path is None:
                    first_face_path = file_path
                    save_face_image(student_id, first_face_path)   # NEW
                    print(f"📸 Face image saved in DB for student {name} ({reg_no})")

                count += 1

        # Show instructions and counter
        cv2.putText(frame, "Press 's' to START, 'q' to QUIT", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Photos Captured: {count}/{max_photos}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Enrollment - Capture Student Photos", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("s"):
            capturing = True
        elif key == ord("q") or count >= max_photos:
            break

    cam.release()
    cv2.destroyAllWindows()
    print(f"✅ Enrollment completed. {count} photos saved in {folder}")


if __name__ == "__main__":
    init_db()
    name = input("Enter Name : ").capitalize()
    reg_no = input("Enter Reg :")
    dept = input("Enter Dept :").upper()
    class_name = input("Enter Class :")
    password = input("Set Password for Student Login (leave blank for auto-generate): ") or None

    capture_student_photos(name, reg_no, dept, class_name, password, max_photos=100)
