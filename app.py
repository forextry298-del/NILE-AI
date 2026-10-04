import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "nile_ai.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

PRODUCTS = [
    {"name":"E-1","price":30000,"days":24,"daily":4500,"total":108000},
    {"name":"E-2","price":70000,"days":23,"daily":10850,"total":249550},
    {"name":"E-3","price":100000,"days":22,"daily":16000,"total":352000},
    {"name":"E-4","price":270000,"days":21,"daily":44550,"total":935550},
    {"name":"E-5","price":600000,"days":20,"daily":102000,"total":2040000},
    {"name":"E-6","price":1000000,"days":19,"daily":175000,"total":3325000},
    {"name":"E-7","price":2000000,"days":18,"daily":360000,"total":6480000},
    {"name":"E-8","price":5000000,"days":17,"daily":925000,"total":15725000},
]

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nickname TEXT DEFAULT 'Anon',
        balance REAL DEFAULT 0,
        wallet REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT, price REAL,
        days INTEGER, daily REAL, total REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, type TEXT, amount REAL, status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER, member_phone TEXT,
        level INTEGER DEFAULT 1, deposited INTEGER DEFAULT 0
    )""")
    c.commit()
    c.close()

init_db()

def me():
    uid = session.get("uid")
    if not uid:
        return None
    c = conn()
    u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    c.close()
    return u

@app.context_processor
def common():
    return {"user": me(), "products": PRODUCTS}

def auth():
    return bool(me())

@app.route("/")
def index():
    return redirect(url_for("home") if auth() else url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        phone = request.form.get("phone","").strip()
        password = request.form.get("password","")
        confirm = request.form.get("confirm","")
        if not phone or not password:
            flash("Phone number and password are required.")
            return redirect(url_for("register"))
        if password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for("register"))
        try:
            c = conn()
            cur = c.execute("INSERT INTO users(phone,password) VALUES(?,?)", (phone,password))
            uid = cur.lastrowid
            invite = request.form.get("invite","").strip()
            if invite:
                c.execute("INSERT INTO referrals(owner_id,member_phone) VALUES(?,?)", (uid,invite))
            c.commit()
            c.close()
            flash("Registration successful.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That phone number is already registered.")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone","").strip()
        password = request.form.get("password","")
        c = conn()
        u = c.execute("SELECT * FROM users WHERE phone=? AND password=?", (phone,password)).fetchone()
        c.close()
        if u:
            session["uid"] = u["id"]
            return redirect(url_for("home"))
        flash("Invalid phone number or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/home")
def home():
    if not auth(): return redirect(url_for("login"))
    return render_template("home.html")

@app.route("/products")
def products():
    if not auth(): return redirect(url_for("login"))
    return render_template("products.html")

@app.route("/product/<name>")
def product(name):
    if not auth(): return redirect(url_for("login"))
    p = next((x for x in PRODUCTS if x["name"] == name), None)
    if not p: return "Product not found", 404
    return render_template("product.html", p=p)

@app.route("/product/<name>/purchase", methods=["POST"])
def purchase(name):
    if not auth(): return redirect(url_for("login"))
    p = next((x for x in PRODUCTS if x["name"] == name), None)
    if not p: return "Product not found", 404
    u = me()
    if (u["balance"] or 0) < p["price"]:
        flash("Insufficient balance.")
        return redirect(url_for("product", name=name))
    c = conn()
    c.execute("UPDATE users SET balance=balance-? WHERE id=?", (p["price"],u["id"]))
    c.execute("""INSERT INTO purchases(user_id,product,price,days,daily,total)
                 VALUES(?,?,?,?,?,?)""",
              (u["id"],p["name"],p["price"],p["days"],p["daily"],p["total"]))
    c.commit()
    c.close()
    flash("Product added.")
    return redirect(url_for("income"))

@app.route("/income")
def income():
    if not auth(): return redirect(url_for("login"))
    c = conn()
    rows = c.execute("SELECT * FROM purchases WHERE user_id=? ORDER BY id DESC",(me()["id"],)).fetchall()
    c.close()
    return render_template("income.html", rows=rows)

@app.route("/my")
def my():
    if not auth(): return redirect(url_for("login"))
    c = conn()
    refs = c.execute("SELECT * FROM referrals WHERE owner_id=? ORDER BY id DESC",(me()["id"],)).fetchall()
    c.close()
    return render_template("my.html", refs=refs)

@app.route("/team")
def team():
    if not auth(): return redirect(url_for("login"))
    c = conn()
    refs = c.execute("SELECT * FROM referrals WHERE owner_id=? ORDER BY id DESC",(me()["id"],)).fetchall()
    c.close()
    return render_template("team.html", refs=refs)

@app.route("/vip-task")
def vip_task():
    if not auth(): return redirect(url_for("login"))
    tasks=[(1,5,15000),(2,15,30000),(3,40,100000),(4,80,200000),(5,150,500000),(6,250,800000)]
    return render_template("vip.html", tasks=tasks)

@app.route("/deposit", methods=["GET","POST"])
def deposit():
    if not auth(): return redirect(url_for("login"))
    if request.method == "POST":
        try: amount=float(request.form.get("amount") or 0)
        except ValueError: amount=0
        if amount < 1000:
            flash("Minimum deposit request is UGX 1,000.")
        else:
            flash("Deposit request recorded for review.")
    return render_template("deposit.html")

@app.route("/withdraw", methods=["GET","POST"])
def withdraw():
    if not auth(): return redirect(url_for("login"))
    if request.method == "POST":
        try: amount=float(request.form.get("amount") or 0)
        except ValueError: amount=0
        u=me()
        if amount < 5000:
            flash("Minimum withdrawal is UGX 5,000.")
        elif amount > (u["balance"] or 0):
            flash("Insufficient balance.")
        else:
            c=conn()
            c.execute("INSERT INTO transactions(user_id,type,amount,status) VALUES(?,?,?,?)",
                      (u["id"],"Withdraw",amount,"Pending review"))
            c.execute("UPDATE users SET balance=balance-? WHERE id=?",(amount,u["id"]))
            c.commit(); c.close()
            flash("Withdrawal request submitted for review.")
    return render_template("withdraw.html")

@app.route("/bills")
def bills():
    if not auth(): return redirect(url_for("login"))
    c=conn()
    rows=c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC",(me()["id"],)).fetchall()
    c.close()
    return render_template("bills.html", rows=rows)

@app.route("/chat")
def chat():
    if not auth(): return redirect(url_for("login"))
    return render_template("chat.html")

@app.route("/settings")
def settings():
    if not auth(): return redirect(url_for("login"))
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
