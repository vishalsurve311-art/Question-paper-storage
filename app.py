import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)

# ─── Secret Key ───────────────────────────────────────────────────────────────
app.secret_key = os.environ.get("SECRET_KEY", "changeme_in_production_32bytes!!")

# ─── MySQL Config ─────────────────────────────────────────────────────────────
app.config["MYSQL_HOST"]     = os.environ.get("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"]     = os.environ.get("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"]       = os.environ.get("MYSQL_DB", "question_bank")
app.config["MYSQL_PORT"]     = int(os.environ.get("MYSQL_PORT", 3306))
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

# ─── Global Error Handler ───────────────────────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e

    # Handle non-HTTP exceptions only
    print(f"CRITICAL ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


# ─── Upload Config ────────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024   # 50 MB limit

# Pre-hashed password for "1234" — generated once at startup
TEACHER_PASSWORD_HASH = generate_password_hash("1234")

# ─── Auth decorator ───────────────────────────────────────────────────────────
def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("teacher_logged_in"):
            return jsonify({"error": "Unauthorized. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Page Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("student.html")


@app.route("/teacher")
def teacher_page():
    return render_template("teacher.html")


@app.route("/student")
def student_page():
    return render_template("student.html")


# ─── API: Login ───────────────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if check_password_hash(TEACHER_PASSWORD_HASH, password):
        session["teacher_logged_in"] = True
        return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid password"}), 401


# ─── API: Logout ──────────────────────────────────────────────────────────────
@app.route("/logout", methods=["POST"])
def logout():
    session.pop("teacher_logged_in", None)
    return jsonify({"success": True, "message": "Logged out"})


# ─── API: Check session ───────────────────────────────────────────────────────
@app.route("/session-status", methods=["GET"])
def session_status():
    return jsonify({"logged_in": bool(session.get("teacher_logged_in"))})


# ─── API: Upload ──────────────────────────────────────────────────────────────
@app.route("/upload", methods=["POST"])
@teacher_required
def upload():
    # Validate file presence
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Gather metadata
    year      = request.form.get("year", "").strip()
    semester  = request.form.get("semester", "").strip()
    branch    = request.form.get("branch", "").strip()
    subject   = request.form.get("subject", "").strip()
    exam_type = request.form.get("exam_type", "").strip()
    month     = request.form.get("month", "").strip()

    if not all([year, semester, branch, subject, exam_type, month]):
        return jsonify({"error": "All metadata fields are required"}), 400

    # Save file with a unique prefix to prevent collisions
    original_name = secure_filename(file.filename)
    unique_name   = f"{uuid.uuid4().hex}_{original_name}"
    save_path     = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    
    try:
        file.save(save_path)
    except Exception as e:
        print(f"FILE SAVE ERROR: {str(e)}")
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

    # Persist to DB
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """INSERT INTO papers (year, semester, branch, subject, exam_type, month, file_path)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (year, semester, branch, subject, exam_type, month, unique_name)
        )
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        os.remove(save_path)   # rollback file if DB insert fails
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"success": True, "message": "Paper uploaded successfully", "filename": unique_name})


# ─── API: Search ──────────────────────────────────────────────────────────────
@app.route("/search", methods=["GET"])
def search():
    year      = request.args.get("year", "").strip()
    semester  = request.args.get("semester", "").strip()
    branch    = request.args.get("branch", "").strip()
    subject   = request.args.get("subject", "").strip()
    exam_type = request.args.get("exam_type", "").strip()
    month     = request.args.get("month", "").strip()

    conditions = []
    params     = []

    if year:
        conditions.append("year = %s");      params.append(year)
    if semester:
        conditions.append("semester = %s");  params.append(semester)
    if branch:
        conditions.append("branch LIKE %s"); params.append(f"%{branch}%")
    if subject:
        conditions.append("subject LIKE %s"); params.append(f"%{subject}%")
    if exam_type:
        conditions.append("exam_type = %s"); params.append(exam_type)
    if month:
        conditions.append("month = %s");     params.append(month)

    query = "SELECT * FROM papers"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"

    try:
        cur = mysql.connection.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"success": True, "papers": rows})


# ─── API: Delete paper (teacher only) ────────────────────────────────────────
@app.route("/delete/<int:paper_id>", methods=["DELETE"])
@teacher_required
def delete_paper(paper_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT file_path FROM papers WHERE id = %s", (paper_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Paper not found"}), 404

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], row["file_path"])
        cur.execute("DELETE FROM papers WHERE id = %s", (paper_id,))
        mysql.connection.commit()
        cur.close()

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": True, "message": "Paper deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── File Serving ─────────────────────────────────────────────────────────────
@app.route("/uploads/<path:filename>")
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
