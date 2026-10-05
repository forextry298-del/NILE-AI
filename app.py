from flask import Flask,render_template,request,redirect,url_for,session
import sqlite3,os
app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY","nile-ai-secret")
DB="nile_ai.db"
def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init_db():
 c=db();c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,phone TEXT UNIQUE NOT NULL,password TEXT NOT NULL,nickname TEXT DEFAULT  ,points INTEGER DEFAULT 0)");c.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,points INTEGER)");c.executemany("INSERT OR IGNORE INTO tasks(id,name,points) VALUES(?,?,?)",[(1,"AI Learning",50),(2,"Daily Check-in",20),(3,"Complete Profile",30)]);c.commit();c.close()
init_db()
@app.route("/")
def index(): return redirect(url_for("home" if session.get("uid") else "login"))
@app.route("/register",methods=["GET","POST"])
def register():
 if request.method=="POST":
  try:
   c=db();c.execute("INSERT INTO users(phone,password,nickname) VALUES(?,?,?)",(request.form["phone"],request.form["password"],request.form.get("nickname","Anon")));c.commit();c.close();return redirect(url_for("login"))
  except sqlite3.IntegrityError:return "Phone already registered"
 return render_template("register.html")
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  c=db();u=c.execute("SELECT * FROM users WHERE phone=? AND password=?",(request.form["phone"],request.form["password"])).fetchone();c.close()
  if u:session["uid"]=u["id"];return redirect(url_for("home"))
  return "Invalid login"
 return render_template("login.html")
def current_user():
 if not session.get("uid"):return None
 c=db();u=c.execute("SELECT * FROM users WHERE id=?",(session["uid"],)).fetchone();c.close();return u
@app.route("/home")
def home():
 u=current_user()
 if not u:return redirect(url_for("login"))
 return render_template("home.html",user=u)
@app.route("/logout")
def logout():session.clear();return redirect(url_for("login"))
@app.route("/ai")
def ai():
 if not current_user():return redirect(url_for("login"))
 return render_template("ai.html")
@app.route("/tasks")
def tasks():
 u=current_user()
 if not u:return redirect(url_for("login"))
 c=db();items=c.execute("SELECT * FROM tasks").fetchall();c.close();return render_template("tasks.html",tasks=items,user=u)
@app.route("/profile")
def profile():
 u=current_user()
 if not u:return redirect(url_for("login"))
 return render_template("profile.html",user=u)
@app.route("/team")
def team():
 if not current_user():return redirect(url_for("login"))
 return render_template("team.html")
if __name__=="__main__":app.run(host="0.0.0.0",port=5000)
