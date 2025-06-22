from flask import Flask, render_template, request, redirect, url_for, session,flash
from flaskwebgui import FlaskUI
import sqlite3
import os
import traceback 
import base64
import cv2
import numpy as np
from flask import jsonify



app = Flask(__name__)
app.secret_key = 'phani_3588'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('auth'))
    return render_template('home.html')


@app.route('/auth', methods=['GET'])
def auth():
    return render_template('SignUp_LogIn_Form.html')


@app.route('/login', methods=['POST'])
def login_user():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()

    if result:
        session['user'] = username
        return redirect(url_for('home'))
    else:
        flash("❌ Invalid credentials!","error")
        return redirect(url_for('home'))


@app.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT)')

    # Check for existing username or email
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        flash("⚠️ Username already exists! Please choose another one.", "error")
        return redirect(url_for('auth'))

    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        flash("❌ Email is already registered. Try logging in.", "error")
        return redirect(url_for('auth'))

    # Now safe to insert
    c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
              (username, email, password))
    conn.commit()
    conn.close()

    flash("✅ Registration successful! Please log in.", "success")
    return redirect(url_for('auth'))




@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth'))


@app.route('/enroll_live', methods=['POST'])
def enroll_live():
    if 'user' not in session:
        return redirect(url_for('auth'))

    try:
        import cv2
        from models.model1_enroll_live import process_live_enrollment

        student_id = request.form['Student_ID']
        name = request.form['Student_Name']
        student_class = request.form['class']
        branch = request.form['branch']

        process_live_enrollment({
            "student_id": student_id,
            "name": name,
            "student_class": student_class,
            "branch": branch
        })

        flash(f"✅ {name} enrolled successfully via webcam!", "success")

    except Exception as e:
        import traceback
        print("Live Enrollment Error:", e)
        traceback.print_exc()
        flash(f"❌ Live Enrollment failed: {str(e)}", "error")

    return redirect(url_for('home'))





@app.route('/attendance_live', methods=['POST'])
def attendance_live():
    if 'user' not in session:
        return redirect(url_for('auth'))

    try:
        import cv2
        from models.model2_attendance_live import mark_attendance_live

        subject = request.form['subject']
        print("[INFO] Starting live attendance for subject:", subject)

        result = mark_attendance_live(subject)
        flash(f"✅ Attendance recorded for {len(result)} student(s) in {subject}.", "success")

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"❌ Live Attendance failed: {str(e)}", "error")

    return redirect(url_for('home'))



@app.route('/view_sheet', methods=['GET', 'POST'])
def view_sheet():
    if 'user' not in session:
        return redirect(url_for('auth'))

    import csv
    import sqlite3
    from collections import defaultdict

    records = []
    all_subjects = set()
    all_dates = set()

    # Load student classes from DB
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("SELECT id, class FROM students")
    student_classes = {sid: cls for sid, cls in c.fetchall()}
    conn.close()

    # Parse attendance_logs.csv
    try:
        with open('attendance_logs.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    sid, subject, timestamp = row[0], row[1], row[2]
                    student_class = student_classes.get(sid, "N/A")
                    date = timestamp.split()[0]

                    all_subjects.add(subject)
                    all_dates.add(date)

                    records.append({
                        'sid': sid,
                        'subject': subject,
                        'timestamp': timestamp,
                        'class': student_class,
                        'date': date
                    })
    except FileNotFoundError:
        pass

    # Get filter inputs
    selected_subject = request.form.get('subject', '')
    selected_date = request.form.get('date', '')

    # Apply filters
    filtered_records = [
        r for r in records
        if (not selected_subject or r['subject'] == selected_subject) and
           (not selected_date or r['date'] == selected_date)
    ]

    # Sort
    filtered_records.sort(key=lambda x: (x['class'], x['timestamp']))

    return render_template("view_sheet.html",
                           records=filtered_records,
                           subjects=sorted(all_subjects),
                           dates=sorted(all_dates),
                           selected_subject=selected_subject,
                           selected_date=selected_date)


@app.route('/summary_sheet', methods=['GET', 'POST'])
def summary_sheet():
    if 'user' not in session:
        return redirect(url_for('auth'))

    import csv
    from collections import defaultdict

    summary = defaultdict(lambda: defaultdict(int))  # {student_id: {subject: count}}
    all_subjects = set()
    all_ids = set()

    try:
        with open('attendance_logs.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    sid, subject, _ = row[0], row[1], row[2]
                    summary[sid][subject] += 1
                    all_subjects.add(subject)
                    all_ids.add(sid)
    except FileNotFoundError:
        pass

    # Get selected filters from form
    selected_subject = request.form.get('subject', '')
    selected_id = request.form.get('student_id', '')

    # Flatten + filter summary
    summary_list = []
    for sid in summary:
        for subject in summary[sid]:
            if (not selected_subject or subject == selected_subject) and \
               (not selected_id or sid == selected_id):
                summary_list.append((sid, subject, summary[sid][subject]))

    summary_list.sort(key=lambda x: (x[0], x[1]))

    return render_template("summary_sheet.html",
                           summary=summary_list,
                           subjects=sorted(all_subjects),
                           ids=sorted(all_ids),
                           selected_subject=selected_subject,
                           selected_id=selected_id)



@app.route('/export_sheet', methods=['POST'])
def export_sheet():
    if 'user' not in session:
        return redirect(url_for('auth'))

    import csv
    import sqlite3
    from io import StringIO
    from flask import Response

    selected_subject = request.form.get('subject', '')
    selected_date = request.form.get('date', '')

    # Load student class info
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("SELECT id, class FROM students")
    student_classes = {sid: cls for sid, cls in c.fetchall()}
    conn.close()

    # Load and filter attendance
    filtered_rows = []
    try:
        with open('attendance_logs.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    sid, subject, timestamp = row[0], row[1], row[2]
                    date = timestamp.split()[0]
                    student_class = student_classes.get(sid, "N/A")

                    if (not selected_subject or subject == selected_subject) and \
                       (not selected_date or date == selected_date):
                        filtered_rows.append([sid, subject, timestamp, student_class])
    except FileNotFoundError:
        pass

    # Create downloadable CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Subject", "Timestamp", "Class"])
    writer.writerows(filtered_rows)

    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=attendance_export.csv"})


@app.route('/sync_attendance')
def sync_attendance():
    if 'user' not in session:
        return redirect(url_for('auth'))

    import csv
    import sqlite3
    import os
    import time
    from collections import defaultdict
    from datetime import datetime

    csv_path = 'attendance_logs.csv'
    db_path = 'database/users.db'
    last_sync_file = 'last_sync.txt'
    sync_interval_seconds = 12 * 3600  # 12 hours

    # ⏱️ Check if syncing too soon
    if os.path.exists(last_sync_file):
        with open(last_sync_file, 'r') as f:
            try:
                last_time = float(f.read().strip())
                elapsed = time.time() - last_time
                if elapsed < sync_interval_seconds:
                    hours_left = round((sync_interval_seconds - elapsed) / 3600, 2)
                    flash(f"🕒 Sync already done. Try again in {hours_left} hour(s).", "error")
                    return redirect(url_for('home'))
            except:
                pass  # continue if file is malformed

    # ❌ No attendance log
    if not os.path.exists(csv_path):
        flash("⚠️ No new attendance logs to sync.", "error")
        return redirect(url_for('home'))

    # ✅ Open DB
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Load all student info
    c.execute("SELECT id, name, class FROM students")
    student_info = {row[0]: {"name": row[1], "class": row[2]} for row in c.fetchall()}

    # Load attendance logs
    attendance_data = defaultdict(lambda: defaultdict(list))  # class → subject → [(sid, date)]
    with open(csv_path, 'r') as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            sid, subject, timestamp = row[0], row[1].strip().upper(), row[2]
            if sid not in student_info:
                continue
            date_str = timestamp.split()[0]
            student_class = student_info[sid]['class'].upper()
            attendance_data[student_class][subject].append((sid, date_str))

    # Sync to subject tables with 1/0 values
    for s_class, subjects in attendance_data.items():
        for subject, records in subjects.items():
            table_name = f"{s_class}_{subject}"
            present_by_date = defaultdict(set)  # date → set of present student_ids

            for sid, date in records:
                present_by_date[date].add(sid)

            all_dates = sorted(present_by_date.keys())

            # Build columns
            date_columns = [f"'{d}' INTEGER DEFAULT 0" for d in all_dates]
            c.execute(f"""
                CREATE TABLE IF NOT EXISTS '{table_name}' (
                    ID TEXT PRIMARY KEY,
                    Name TEXT,
                    {', '.join(date_columns)}
                )
            """)

            # Ensure date columns exist
            c.execute(f"PRAGMA table_info('{table_name}')")
            existing_cols = {row[1] for row in c.fetchall()}
            for date in all_dates:
                if date not in existing_cols:
                    c.execute(f"ALTER TABLE '{table_name}' ADD COLUMN '{date}' INTEGER DEFAULT 0")

            # All students in class
            class_students = {
                sid: info['name']
                for sid, info in student_info.items()
                if info['class'].upper() == s_class
            }

            # Insert missing students into table
            for sid, sname in class_students.items():
                c.execute(f"SELECT 1 FROM '{table_name}' WHERE ID = ?", (sid,))
                if not c.fetchone():
                    placeholders = ', '.join(['0'] * len(all_dates))
                    c.execute(f"""
                        INSERT INTO '{table_name}' (ID, Name, {', '.join(f"'{d}'" for d in all_dates)})
                        VALUES (?, ?, {placeholders})
                    """, (sid, sname))

            # Update attendance: 1 = present, 0 = absent
            for date, present_ids in present_by_date.items():
                for sid in class_students:
                    value = 1 if sid in present_ids else 0
                    c.execute(f"""
                        UPDATE '{table_name}' SET '{date}' = ? WHERE ID = ?
                    """, (value, sid))

    conn.commit()
    conn.close()

    # ✅ Save sync time & clear log
    with open(last_sync_file, 'w') as f:
        f.write(str(time.time()))
    os.remove(csv_path)

    flash("✅ Attendance synced successfully. Log cleared. Next sync available after 12 hours.", "success")
    return redirect(url_for('home'))



@app.route('/sync_attendance_manual')
def sync_attendance_manual():

    if 'user' not in session:
        return redirect(url_for('auth'))

    import sqlite3
    import csv
    import os
    from collections import defaultdict, Counter
    from datetime import datetime

    db_path = 'database/users.db'
    csv_path = 'attendance_logs.csv'

    if not os.path.exists(csv_path):
        flash("❌ No attendance logs found to sync.", "error")
        return redirect(url_for('home'))

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Load student info
    c.execute("SELECT id, name, class FROM students")
    student_info = {row[0]: {"name": row[1], "class": row[2]} for row in c.fetchall()}

    # Read and group attendance by class and subject
    attendance_data = defaultdict(lambda: defaultdict(list))  # class -> subject -> [(id, date)]
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            sid, subject, timestamp = row[0], row[1].strip(), row[2]
            subject = subject.upper()
            date_str = timestamp.split()[0]

            if sid not in student_info:
                continue  # Skip unknown student

            student_class = student_info[sid]['class'].upper()
            attendance_data[student_class][subject].append((sid, date_str))

    # Process and sync to DB
    for s_class, subjects in attendance_data.items():
        for subject, records in subjects.items():
            table_name = f"{s_class}_{subject}"
            session_counts = Counter()
            expanded_dates = []

            for sid, date in records:
                session_counts[date] += 1
                label = date if session_counts[date] == 1 else f"{date}({session_counts[date]})"
                expanded_dates.append((sid, label))

            all_labels = sorted(set(label for _, label in expanded_dates))

            # Create subject table with dynamic columns
            date_columns = [f"'{label}' INTEGER DEFAULT 0" for label in all_labels]
            c.execute(f"""
                CREATE TABLE IF NOT EXISTS '{table_name}' (
                    ID TEXT PRIMARY KEY,
                    Name TEXT,
                    {', '.join(date_columns)}
                )
            """)

            # Add new columns if any
            c.execute(f"PRAGMA table_info('{table_name}')")
            existing_cols = {row[1] for row in c.fetchall()}

            for label in all_labels:
                if label not in existing_cols:
                    c.execute(f"ALTER TABLE '{table_name}' ADD COLUMN '{label}' INTEGER DEFAULT 0")

            # Insert or update rows
            for sid, label in expanded_dates:
                name = student_info[sid]['name']

                # Check row
                c.execute(f"SELECT * FROM '{table_name}' WHERE ID = ?", (sid,))
                row = c.fetchone()

                if not row:
                    col_defaults = ', '.join(['0'] * len(all_labels))
                    c.execute(f"""
                        INSERT INTO '{table_name}' (ID, Name, {', '.join(f"'{lbl}'" for lbl in all_labels)})
                        VALUES (?, ?, {col_defaults})
                    """, (sid, name))

                # Increment session value
                c.execute(f"SELECT \"{label}\" FROM '{table_name}' WHERE ID = ?", (sid,))
                current = c.fetchone()[0] or 0
                c.execute(f"""
                    UPDATE '{table_name}' SET "{label}" = ? WHERE ID = ?
                """, (current + 1, sid))

    conn.commit()
    conn.close()
    flash("✅ Attendance synced to database successfully!", "success")
    return redirect(url_for('home'))



@app.route('/export_sheet')
def export_page():
    if 'user' not in session:
        return redirect(url_for('auth'))

    import sqlite3
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    conn.close()

    # Detect subject tables like 3F_AI
    class_subject_map = {}
    for table in tables:
        if '_' in table and table[0].isdigit():
            cls, subject = table.split('_', 1)
            cls = cls.upper()
            subject = subject.upper()
            class_subject_map.setdefault(cls, []).append(subject)

    return render_template("export_dropdown.html", class_subject_map=class_subject_map)

@app.route('/query_solver')
def query_solver():
    if 'user' not in session:
        return redirect(url_for('auth'))
    return redirect('https://dquery-gen-viewer-bypk.streamlit.app/')


@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    try:
        data = request.get_json()
        subject = data['subject'].strip().upper()
        image_data = data['image'].split(',')[1]
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(image_data), np.uint8), cv2.IMREAD_COLOR)

        matched_id = mark_attendance_browser(frame, subject)
        if matched_id:
            return jsonify({"message": f"✅ Marked: {matched_id}"})
        else:
            return jsonify({"message": "❌ No match"})
    except Exception as e:
        return jsonify({"message": f"Error: {e}"})
    

@app.route('/upload_enroll_frame', methods=['POST'])
def upload_enroll_frame():
    import base64
    import numpy as np
    data = request.get_json()
    image_data = data['image'].split(',')[1]
    frame = cv2.imdecode(np.frombuffer(base64.b64decode(image_data), np.uint8), cv2.IMREAD_COLOR)

    student_info = {
        "student_id": data["student_id"],
        "name": data["name"],
        "student_class": data["student_class"],
        "branch": data["branch"]
    }

    result = save_enroll_snapshot(frame, student_info)
    return jsonify({"message": result})


# @app.route('/about')
# def about():
#     return render_template('about.html')

if __name__ == "__main__":
    # import webbrowser
    # import threading

    # def open_browser():
    #     webbrowser.open_new("http://127.0.0.1:5000")

    # threading.Timer(1.5, open_browser).start()
    # app.run(host="127.0.0.1", port=5000, debug=False)
    ui = FlaskUI(app=app, server="flask", width=1024, height=768)
    ui.run()

