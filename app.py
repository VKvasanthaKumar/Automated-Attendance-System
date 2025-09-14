from flask import Flask, render_template, redirect, url_for, request, flash ,session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3

import cv2
import numpy as np

from attendance import recognize_student_live



from deepface import DeepFace
from database.helpers import load_face_images
import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


DB_PATH = "database/attendance.db"

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("database/attendance.db")
    cur = conn.cursor()
    cur.execute("SELECT id, name, 'student' as role FROM students WHERE id=?", (user_id,))
    user = cur.fetchone()
    if not user:
        cur.execute("SELECT id, name, 'faculty' as role FROM faculty WHERE id=?", (user_id,))
        user = cur.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        if role == "student":
            cur.execute("SELECT id, name FROM students WHERE reg_no=? AND password=?", (username, password))
        else:
            cur.execute("SELECT id, name FROM faculty WHERE staff_id=? AND password=?", (username, password))

        user = cur.fetchone()
        conn.close()

        if user:
            login_user(User(user[0], user[1], role))
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials!")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome {current_user.username}! Role: {current_user.role}"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))



# ---------------- Faculty Dashboard ----------------

# ---------------- Faculty Register ----------------
@app.route("/faculty/register", methods=["GET", "POST"])
def faculty_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO faculty (name, email, password) VALUES (?, ?, ?)",
                        (name, email, password))
            conn.commit()
            flash("✅ Faculty registered successfully! Please login.")
        except sqlite3.IntegrityError:
            flash("⚠️ Email already exists! Please login instead.")
        finally:
            conn.close()

        return redirect(url_for("faculty_login"))

    return render_template("faculty_register.html")


# ---------------- Faculty Login ----------------
@app.route("/faculty/login", methods=["GET", "POST"])
def faculty_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM faculty WHERE email=? AND password=?", (email, password))
        faculty = cur.fetchone()
        conn.close()

        if faculty:
            session["faculty_id"] = faculty[0]
            session["faculty_name"] = faculty[1]
            flash(f"👋 Welcome {faculty[1]}")
            return redirect(url_for("faculty_dashboard"))
        else:
            flash("❌ Invalid credentials!")

    return render_template("faculty_login.html")


# ---------------- Faculty Dashboard ----------------
@app.route("/faculty/dashboard", methods=["GET", "POST"])
def faculty_dashboard():
    if "faculty_id" not in session:
        flash("⚠️ Please login first.")
        return redirect(url_for("faculty_login"))

    faculty_id = session["faculty_id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Upload lesson
    if request.method == "POST":
        topic = request.form["topic"]
        date = datetime.date.today().isoformat()
        cur.execute("INSERT INTO lessons (faculty_id, topic, date) VALUES (?, ?, ?)",
                    (faculty_id, topic, date))
        conn.commit()
        flash("✅ Lesson uploaded successfully!")

    # Lessons list
    cur.execute("SELECT topic, date FROM lessons WHERE faculty_id=?", (faculty_id,))
    lessons = cur.fetchall()

    # Attendance records
    cur.execute("""
        SELECT s.name, s.reg_no, a.date, a.status
        FROM students s
        JOIN attendance a ON s.id = a.student_id
        WHERE a.faculty_id=?
        ORDER BY a.date DESC
    """, (faculty_id,))
    attendance_records = cur.fetchall()

    # Today's present count
    today = datetime.date.today().isoformat()
    cur.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE faculty_id=? AND date=? AND status='Present'
    """, (faculty_id, today))
    today_present = cur.fetchone()[0]

    # Each student’s overall attendance percentage
    cur.execute("""
        SELECT s.name, s.reg_no,
               ROUND((SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0 / COUNT(*)), 2) as percentage
        FROM students s
        JOIN attendance a ON s.id = a.student_id
        WHERE a.faculty_id=?
        GROUP BY s.id
    """, (faculty_id,))
    student_percentages = cur.fetchall()

    # Low attendance (<75%)
    cur.execute("""
        SELECT s.name, s.reg_no,
               ROUND((SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0 / COUNT(*)), 2) as percentage
        FROM students s
        JOIN attendance a ON s.id = a.student_id
        WHERE a.faculty_id=?
        GROUP BY s.id
        HAVING percentage < 75
    """, (faculty_id,))
    low_attendance = cur.fetchall()

    conn.close()

    return render_template("faculty_dashboard.html",
                           faculty_name=session["faculty_name"],
                           lessons=lessons,
                           attendance_records=attendance_records,
                           today_present=today_present,
                           student_percentages=student_percentages,
                           low_attendance=low_attendance)




#-------------student dashboard-------------------
#login
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        reg_no = request.form["reg_no"]
        password = request.form.get("password")  # can be empty

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Fetch student
        cur.execute("SELECT id, name, class_name, dept, password FROM students WHERE reg_no=?", (reg_no,))
        student = cur.fetchone()
        if not student:
            flash("❌ Invalid Registration Number!")
            conn.close()
            return render_template("student_login.html")

        student_id, name, class_name, dept, stored_password = student

        # First-time login or empty password -> use auto-generated
        if not stored_password or not password:
            password = f"{name}{student_id}"
            cur.execute("UPDATE students SET password=? WHERE id=?", (password, student_id))
            conn.commit()

        # Check password
        if password == stored_password or password == f"{name}{student_id}":
            # Login success
            session["student_id"] = student_id
            session["student_name"] = name
            session["student_class"] = class_name
            session["student_dept"] = dept
            flash(f"👋 Welcome {name}")
            conn.close()
            return redirect(url_for("student_dashboard"))
        else:
            flash("❌ Invalid Password!")
            conn.close()
            return render_template("student_login.html")

    return render_template("student_login.html")


@app.route("/student/forgot_password", methods=["GET", "POST"])
def student_forgot_password():
    if request.method == "POST":
        reg_no = request.form["reg_no"]
        new_password = request.form["new_password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("SELECT id FROM students WHERE reg_no=?", (reg_no,))
        student = cur.fetchone()

        if not student:
            flash("❌ Invalid Registration Number!")
            conn.close()
            return render_template("student_forgot_password.html")

        student_id = student[0]

        # Update password
        cur.execute("UPDATE students SET password=? WHERE id=?", (new_password, student_id))
        conn.commit()
        conn.close()

        flash("✅ Password changed successfully! Use new password to login.")
        return redirect(url_for("student_login"))

    return render_template("student_forgot_password.html")


#dash

@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        flash("⚠️ Please login first.")
        return redirect(url_for("student_login"))

    student_id = session["student_id"]
    student_class = session["student_class"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Attendance stats
    cur.execute("""
        SELECT COUNT(*) FROM attendance WHERE student_id=?
    """, (student_id,))
    total_days = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Present'
    """, (student_id,))
    present_days = cur.fetchone()[0]

    attendance_percentage = round((present_days / total_days * 100), 2) if total_days > 0 else 0

    # Attendance history
    cur.execute("""
        SELECT date, status FROM attendance WHERE student_id=?
        ORDER BY date DESC
    """, (student_id,))
    attendance_history = cur.fetchall()

    # Lessons for student's class uploaded by faculty
    cur.execute("""
        SELECT l.topic, l.date, f.name 
        FROM lessons l
        JOIN faculty f ON f.id = l.faculty_id
        WHERE l.class_name=?
        ORDER BY l.date DESC
    """, (student_class,))
    lessons = cur.fetchall()

    # Quizzes for student's class
    cur.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d FROM quiz
        WHERE class=?
    """, (student_class,))
    quizzes = cur.fetchall()

    # Quiz results
    cur.execute("""
        SELECT q.question, r.selected_option, q.correct_option, r.is_correct
        FROM quiz_results r
        JOIN quiz q ON r.quiz_id = q.id
        WHERE r.student_id=?
    """, (student_id,))
    quiz_results = cur.fetchall()

    conn.close()

    return render_template("student_dashboard.html",
                           student_name=session["student_name"],
                           student_class=student_class,
                           student_dept=session["student_dept"],
                           total_days=total_days,
                           present_days=present_days,
                           attendance_percentage=attendance_percentage,
                           attendance_history=attendance_history,
                           lessons=lessons,
                           quizzes=quizzes,
                           quiz_results=quiz_results)


if __name__ == "__main__":
    app.run(debug=True)
