from flask import Flask, render_template, request, redirect, send_file, session
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "admin123"


# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll TEXT,
        m1 INTEGER,
        m2 INTEGER,
        m3 INTEGER,
        m4 INTEGER,
        m5 INTEGER,
        total INTEGER,
        percent REAL,
        grade TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------- HOME ----------
@app.route('/')
def home():
    return render_template("index.html")


# ---------- ADD PAGE ----------
@app.route('/add')
def add():
    return render_template("add.html")


# ---------- CALCULATE RESULT ----------
@app.route('/result', methods=['POST'])
def result():
    name = request.form['name']
    roll = request.form['roll']

    m1 = int(request.form['m1'] or 0)
    m2 = int(request.form['m2'] or 0)
    m3 = int(request.form['m3'] or 0)
    m4 = int(request.form['m4'] or 0)
    m5 = int(request.form['m5'] or 0)

    total = m1+m2+m3+m4+m5
    percent = round(total/5,2)

    if percent >= 90:
        grade = "A+"
    elif percent >= 75:
        grade = "A"
    elif percent >= 60:
        grade = "B"
    elif percent >= 50:
        grade = "C"
    else:
        grade = "Fail"

    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students
        (name, roll, m1, m2, m3, m4, m5, total, percent, grade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,(name, roll, m1, m2, m3, m4, m5, total, percent, grade))
    conn.commit()
    conn.close()

    return render_template("result.html",
                           name=name,
                           roll=roll,
                           total=total,
                           percent=percent,
                           grade=grade)


# ---------- LOGIN ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['username']=="admin" and request.form['password']=="admin123":
            session['admin'] = True
            return redirect('/students')
        else:
            return "Invalid Login"

    return render_template("login.html")


# ---------- VIEW STUDENTS ----------
@app.route('/students')
def students():
    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM students")
    data = cur.fetchall()
    conn.close()

    return render_template("students.html", students=data)


# ---------- DELETE ----------
@app.route('/delete/<int:id>')
def delete_student(id):
    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/students')


# ---------- EDIT ----------
@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit_student(id):
    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        m1 = int(request.form['m1'])
        m2 = int(request.form['m2'])
        m3 = int(request.form['m3'])
        m4 = int(request.form['m4'])
        m5 = int(request.form['m5'])

        total = m1+m2+m3+m4+m5
        percent = round(total/5,2)

        if percent >= 90:
            grade = "A+"
        elif percent >= 75:
            grade = "A"
        elif percent >= 60:
            grade = "B"
        elif percent >= 50:
            grade = "C"
        else:
            grade = "Fail"

        cur.execute("""
        UPDATE students
        SET name=?, roll=?, m1=?, m2=?, m3=?, m4=?, m5=?, total=?, percent=?, grade=?
        WHERE id=?
        """,(name, roll, m1, m2, m3, m4, m5, total, percent, grade, id))

        conn.commit()
        conn.close()
        return redirect('/students')

    cur.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cur.fetchone()
    conn.close()

    return render_template("edit.html", student=student)


# ---------- SEARCH ----------
@app.route('/search', methods=['GET','POST'])
def search():
    if request.method == 'POST':
        roll = request.form['roll']

        conn = sqlite3.connect("students.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE roll=?", (roll,))
        student = cur.fetchone()
        conn.close()

        if student:
            return render_template("result.html",
                                   name=student[1],
                                   roll=student[2],
                                   total=student[8],
                                   percent=student[9],
                                   grade=student[10])
        else:
            return "No student found"

    return render_template("search.html")

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')
# ---------- PDF DOWNLOAD ----------
@app.route('/download/<int:id>')
def download_pdf(id):
    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cur.fetchone()
    conn.close()

    if not student:
        return "Student not found"

    filename = f"result_{id}.pdf"

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Student Result", styles['Title']))
    elements.append(Spacer(1,12))
    elements.append(Paragraph(f"Name: {student[1]}", styles['Normal']))
    elements.append(Paragraph(f"Roll: {student[2]}", styles['Normal']))
    elements.append(Paragraph(f"Total: {student[8]}", styles['Normal']))
    elements.append(Paragraph(f"Percentage: {student[9]}%", styles['Normal']))
    elements.append(Paragraph(f"Grade: {student[10]}", styles['Normal']))

    doc.build(elements)
    return send_file(filename, as_attachment=True)


# ---------- RUN ----------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
