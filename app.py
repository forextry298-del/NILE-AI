import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")
DB = os.environ.get("DB_PATH", "nile_ai.db")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        invitation TEXT
    )""")
    c.commit()
    return c

@app.route("/")
def home():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        invitation = request.form.get("invitation", "").strip()
        if not phone or not password:
            return render_template("register.html", error="Phone and password are required.")
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")
        c = db()
        try:
            c.execute("INSERT INTO users(phone,password,invitation) VALUES(?,?,?)", (phone, generate_password_hash(password), invitation))
            c.commit()
        except sqlite3.IntegrityError:
            c.close()
            return render_template("register.html", error="Phone number already registered.")
        c.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        c = db()
        user = c.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        c.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["phone"] = user["phone"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid phone number or password.")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", phone=session.get("phone"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
