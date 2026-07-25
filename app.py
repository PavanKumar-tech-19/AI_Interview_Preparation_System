from flask import Flask, render_template, request, redirect, session, send_file
import fitz
import os
from questions import questions
from scoring import evaluate, generate_ai_resume_questions
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
from datetime import datetime
from reportlab.pdfgen import canvas
import io

def init_db():
    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        domain TEXT,
        score REAL,
        interview_date TEXT
    )
    """)

    conn.commit()
    conn.close()

app = Flask(__name__)
app.secret_key = "secret_key_123"

init_db()
 
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, hashed_password)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return render_template(
                "register.html",
                error="Username already exists!"
            )

        conn.close()
        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )

    return render_template("login.html")


# ---------------- HOME ---------------- #

@app.route("/", methods=["GET", "POST"])
def index():

    if "user" not in session:
        return redirect("/login")

    if "domain" not in session:

        if request.method == "POST":
            domain = request.form.get("domain")

            if domain not in questions:
                return redirect("/")

            session["domain"] = domain

            session["selected_questions"] = random.sample(
                questions[domain],
                min(5, len(questions[domain]))
            )

            session["q_index"] = 0
            session["results"] = []

            return redirect("/")

        return render_template(
            "index.html",
            choose_domain=True
        )

    current = session.get("q_index", 0)
    selected_questions = session.get("selected_questions", [])

            # ---------------- INTERVIEW COMPLETED ---------------- #

    if current >= len(selected_questions):

        results = session.get("results", [])

        if results:
            total_score = sum(
                int(r["evaluation"]["score"])
                for r in results
            )
            average = round(total_score / len(results), 1)
        else:
            average = 0

        session["average"] = average

        # Save interview history
        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO interviews(username, domain, score, interview_date) VALUES(?,?,?,?)",
            (
                session["user"],
                session["domain"],
                average,
                datetime.now().strftime("%d-%m-%Y %I:%M %p")
            )
        )

        conn.commit()
        conn.close()

        return redirect("/report")


    # ---------------- SUBMIT ANSWER ---------------- #

    if request.method == "POST":

        answer = request.form.get("answer", "").strip()

        question = selected_questions[current]

        evaluation = evaluate(question, answer)

        results = session.get("results", [])

        results.append({
            "question": question,
            "answer": answer,
            "evaluation": evaluation
        })

        session["results"] = results
        session["q_index"] = current + 1

        return redirect("/")


    # ---------------- SHOW QUESTION ---------------- #

    return render_template(
        "index.html",
        choose_domain=False,
        domain=session["domain"],
        question=selected_questions[current],
        count=current + 1,
        total=len(selected_questions)
    )

    # ---------------- REPORT ---------------- #

@app.route("/report")
def report():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "report.html",
        average=session.get("average", 0),
        results=session.get("results", []),
        domain=session.get("domain", "")
    )

# ---------------- PDF REPORT ---------------- #

@app.route("/download_pdf")
def download_pdf():

    if "user" not in session:
        return redirect("/login")

    pdf = io.BytesIO()

    c = canvas.Canvas(pdf)

    c.setTitle("AI Interview Report")

    c.drawString(100, 800, "AI Interview Preparation System")
    c.drawString(100, 770, "Interview Report")

    c.drawString(
        100,
        730,
        f"User: {session['user']}"
    )

    c.drawString(
        100,
        700,
        f"Domain: {session.get('domain','')}"
    )

    c.drawString(
        100,
        670,
        f"Average Score: {session.get('average',0)}/10"
    )

    y = 630

    for result in session.get("results", []):

        c.drawString(
            100,
            y,
            f"Question: {result['question'][:50]}"
        )

        y -= 30

        c.drawString(
            100,
            y,
            f"Score: {result['evaluation']['score']}/10"
        )

        y -= 40

    c.save()

    pdf.seek(0)

    return send_file(
        pdf,
        as_attachment=True,
        download_name="Interview_Report.pdf",
        mimetype="application/pdf"
    )

# ---------------- RESUME UPLOAD ---------------- #

@app.route("/resume_upload", methods=["GET", "POST"])
def resume_upload():

    if "user" not in session:
        return redirect("/login")

        # if "user" not in session:
#     return redirect("/login")

    if request.method == "POST":

        file = request.files.get("resume")

        if not file or file.filename == "":
            return "Please select a PDF file."

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        doc = fitz.open(filepath)

        resume_text = ""

        for page in doc:
            resume_text += page.get_text()

        doc.close()

        session["resume_text"] = resume_text

        return render_template(
            "resume_questions.html",
            resume_text=resume_text
        )

    return render_template("resume_upload.html")

    # ---------------- GENERATE RESUME QUESTIONS ---------------- #

@app.route("/generate_resume_questions", methods=["POST"])
def generate_resume_questions():

    if "user" not in session:
        return redirect("/login")

    resume_text = session.get("resume_text", "")

    if not resume_text:
        return "Resume not found"

    resume_questions = generate_ai_resume_questions(resume_text)

    session["resume_questions"] = resume_questions

    return render_template(
        "resume_generated_questions.html",
        questions=resume_questions
    )

# ---------------- RESUME MOCK INTERVIEW START ---------------- #

@app.route("/start_resume_interview")
def start_resume_interview():

    if "user" not in session:
        return redirect("/login")

    if "resume_questions" not in session:
        return redirect("/resume_upload")

    session["resume_q_index"] = 0
    session["resume_results"] = []

    return redirect("/resume_interview")

# ---------------- RESUME INTERVIEW ---------------- #

@app.route("/resume_interview", methods=["GET", "POST"])
def resume_interview():

    if "user" not in session:
        return redirect("/login")

    resume_questions = session.get("resume_questions", [])

    if not resume_questions:
        return redirect("/resume_upload")


    current = session.get("resume_q_index", 0)


    # Interview completed

    if current >= len(resume_questions):

        results = session.get("resume_results", [])

        if results:
            total_score = sum(
                int(r["evaluation"]["score"])
                for r in results
            )

            average = round(
                total_score / len(results),
                1
            )

        else:
            average = 0


        session["resume_average"] = average


        # Save Resume Interview History

        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO interviews(username, domain, score, interview_date) VALUES(?,?,?,?)",
            (
                session["user"],
                "Resume Interview",
                average,
                datetime.now().strftime("%d-%m-%Y %I:%M %p")
            )
        )

        conn.commit()
        conn.close()


        return redirect("/resume_report")


    # Submit answer

    if request.method == "POST":

        answer = request.form.get("answer", "").strip()

        question = resume_questions[current]

        evaluation = evaluate(
            question,
            answer
        )


        results = session.get(
            "resume_results",
            []
        )


        results.append({
            "question": question,
            "answer": answer,
            "evaluation": evaluation
        })


        session["resume_results"] = results

        session["resume_q_index"] = current + 1


        return redirect("/resume_interview")


    # Show Question

    return render_template(
        "resume_interview.html",
        question=resume_questions[current],
        count=current + 1,
        total=len(resume_questions)
    )

# ---------------- RESUME REPORT ---------------- #

@app.route("/resume_report")
def resume_report():

    if "user" not in session:
        return redirect("/login")


    return render_template(
        "resume_report.html",
        average=session.get(
            "resume_average",
            0
        ),
        results=session.get(
            "resume_results",
            []
        )
    )

# ---------------- RESET ---------------- #

@app.route("/reset")
def reset():

    session.pop("domain", None)
    session.pop("selected_questions", None)
    session.pop("q_index", None)
    session.pop("results", None)
    session.pop("average", None)

    return redirect("/")

# ---------------- HISTORY ---------------- #

@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT domain, score, interview_date FROM interviews WHERE username=?",
        (session["user"],)
    )

    interviews = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        interviews=interviews
    )

# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    # Total interviews
    cursor.execute(
        "SELECT COUNT(*) FROM interviews WHERE username=?",
        (session["user"],)
    )
    total = cursor.fetchone()[0]

    # Average score
    cursor.execute(
        "SELECT AVG(score) FROM interviews WHERE username=?",
        (session["user"],)
    )
    avg = cursor.fetchone()[0]

    if avg is None:
        avg = 0
    else:
        avg = round(avg, 1)

    # Best score
    cursor.execute(
        "SELECT MAX(score) FROM interviews WHERE username=?",
        (session["user"],)
    )
    best = cursor.fetchone()[0]

    if best is None:
        best = 0

    # Performance chart data
    cursor.execute(
        "SELECT score FROM interviews WHERE username=? ORDER BY id",
        (session["user"],)
    )

    scores = cursor.fetchall()

    score_list = []

    for score in scores:
        score_list.append(score[0])

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        avg=avg,
        best=best,
        scores=score_list
    )

# ---------------- ADMIN PANEL ---------------- #

@app.route("/admin")
def admin():

    if "user" not in session:
        return redirect("/login")


    if session["user"] != ADMIN_USERNAME:
        return "Access Denied"


    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()


    # Total Users
    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )
    total_users = cursor.fetchone()[0]


    # Total Interviews
    cursor.execute(
        "SELECT COUNT(*) FROM interviews"
    )
    total_interviews = cursor.fetchone()[0]


    # Average Score
    cursor.execute(
        "SELECT AVG(score) FROM interviews"
    )

    avg = cursor.fetchone()[0]

    if avg is None:
        avg = 0
    else:
        avg = round(avg, 1)


    # Best Score
    cursor.execute(
        "SELECT MAX(score) FROM interviews"
    )

    best = cursor.fetchone()[0]

    if best is None:
        best = 0

# Registered Users
    cursor.execute(
        "SELECT username FROM users"
    )

    users = cursor.fetchall()


    # Interview Details
    cursor.execute(
        "SELECT username, domain, score, interview_date FROM interviews ORDER BY id DESC"
    )

    interview_data = cursor.fetchall()

    # Domain Statistics

    cursor.execute(
        "SELECT domain, COUNT(*) FROM interviews GROUP BY domain"
    )

    domain_stats = cursor.fetchall()

    domains = []
    counts = []

    for item in domain_stats:
        domains.append(item[0])
        counts.append(item[1])


    conn.close()


    return render_template(
        "admin.html",
        total_users=total_users,
        total_interviews=total_interviews,
        avg=avg,
        best=best,
        users=users,
        interview_data=interview_data,
        domains=domains,
        counts=counts
    )

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)