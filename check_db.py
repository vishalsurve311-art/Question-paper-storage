import os
from flask import Flask
from flask_mysqldb import MySQL
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB", "question_bank")
app.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT", 3306))

mysql = MySQL(app)

def check():
    with app.app_context():
        try:
            cur = mysql.connection.cursor()
            cur.execute("DESCRIBE papers")
            columns = cur.fetchall()
            print("Table 'papers' structure:")
            for col in columns:
                print(col)
            cur.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check()
