import cv2
import os
from deepface import DeepFace
import sqlite3
import datetime
from database.helpers import load_face_images

DB_PATH = "database/attendance.db"

# Store already marked students in current session
marked_today = set()

def mark_attendance_db(reg_no, faculty_id=1, status="Present"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # get student id
    cur.execute("SELECT id FROM students WHERE reg_no=?", (reg_no,))
    result = cur.fetchone()
    msg = ""

    if result:
        student_id = result[0]
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # check if already marked today
        cur.execute(
            "SELECT * FROM attendance WHERE student_id=? AND faculty_id=? AND date=?",
            (student_id, faculty_id, today)
        )
        record = cur.fetchone()

        if record:
            msg = f"⚠️ {reg_no} Already marked"
        else:
            cur.execute(
                "INSERT INTO attendance (student_id, faculty_id, date, status) VALUES (?, ?, ?, ?)",
                (student_id, faculty_id, today, status)
            )
            conn.commit()
            msg = f"✅ Marked Present: {reg_no}"

    conn.close()
    return msg

def recognize_student_live():
    cam = cv2.VideoCapture(0)
    dataset_path = "dataset"
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    known_students = load_face_images()
    for student_id, name, img_path in known_students:
        print(f"Loaded: {name} (ID: {student_id}) -> {img_path}")

    start_attendance = False

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        display_text = "Press 's' to START Attendance | 'q' to QUIT"

        for (x, y, w, h) in faces:
            # Default: unknown face
            face_label = "Unknown"
            color = (0, 0, 255)  # Red rectangle for unknown

            if start_attendance:
                cv2.imwrite("temp.jpg", frame)
                try:
                    result = DeepFace.find(
                        img_path="temp.jpg",
                        db_path=dataset_path,
                        model_name="VGG-Face",
                        enforce_detection=False
                    )

                    if not result[0].empty:
                        matched_path = result[0].iloc[0]['identity']
                        student_folder = os.path.basename(os.path.dirname(matched_path))
                        reg_no, name = student_folder.split("_", 1)

                        if reg_no not in marked_today:
                            msg = mark_attendance_db(reg_no)
                            marked_today.add(reg_no)
                        else:
                            msg = f"⚠️ {name} ({reg_no}) Already marked"

                        face_label = f"{name} ({reg_no})"
                        color = (0, 255, 0)  # Green for recognized
                        display_text = msg
                    else:
                        display_text = "❌ Unknown Person Detected"

                except Exception as e:
                    display_text = "Error detecting face"

            # Draw rectangle and label
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, face_label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Show instructions or attendance info
        cv2.putText(frame, display_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Attendance Camera", frame)
        key = cv2.waitKey(50) & 0xFF  # Increased delay for reliable key press

        if key == ord("s") or key == ord("S"):
            start_attendance = True
        elif key == ord("q") or key == ord("Q"):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    recognize_student_live()
