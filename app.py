from flask import Flask,render_template,request,redirect,url_for,session
import sqlite3,os
app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY","nile-ai-secret")
DB="nile_ai.db"
def db():
 c=sqlite3.connect(DB,timeout=30);c.row_factory=sqlite3.Row;c.execute("PRAGMA busy_timeout=30000");return c
def init_db():
 c=db();c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,phone TEXT UNIQUE NOT NULL,password TEXT NOT NULL,nickname TEXT DEFAULT '' ,points INTEGER DEFAULT 0)");c.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,points INTEGER)");c.executemany("INSERT OR IGNORE INTO tasks(id,name,points) VALUES(?,?,?)",[(1,"AI Learning",50),(2,"Daily Check-in",20),(3,"Complete Profile",30)]);c.commit();c.close()
init_db()
@app.route("/")
def index(): return redirect(url_for("home" if session.get("uid") else "login"))
@app.route("/register",methods=["GET","POST"])
def register():
 if request.method=="POST":
  phone=request.form.get("phone","").strip()
  password=request.form.get("password","")
  confirm=request.form.get("confirm_password","")
  nickname=request.form.get("nickname","Anon").strip() or "Anon"
  if len(password)<8 or not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
   return render_template("register.html",error="Password must be at least 8 characters and contain uppercase, lowercase and a number.")
  if password!=confirm:
   return render_template("register.html",error="Passwords do not match.")
  try:
   c=db();c.execute("INSERT INTO users(phone,password,nickname) VALUES(?,?,?)",(phone,password,nickname));c.commit();c.close();return render_template("login.html",success="Registration Successful")
  except sqlite3.IntegrityError:
   return render_template("register.html",error="Phone already registered")
 return render_template("register.html")
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  c=db();u=c.execute("SELECT * FROM users WHERE phone=? AND password=?",(request.form["phone"],request.form["password"])).fetchone();c.close()
  if u:session["uid"]=u["id"];session["welcome_popup"]=True;return render_template("login.html",success="Login successful",redirect_home=True)
  return render_template("login.html",error="Please provide valid information to continue")
 return render_template("login.html")
def current_user():
 if not session.get("uid"):return None
 c=db();u=c.execute("SELECT * FROM users WHERE id=?",(session["uid"],)).fetchone();c.close();return u
@app.route("/home")
def home():
 u=current_user()
 if not u:return redirect(url_for("login"))
 return render_template("home.html",user=u)
@app.route("/announcement")
def announcement():
 if not current_user():return redirect(url_for("login"))
 return render_template("announcement.html")
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
@app.route("/raffle")
def raffle():
 u=current_user()
 if not u:return redirect(url_for("login"))
 return render_template("raffle.html",user=u)
@app.route("/settings")
def settings():
 u=current_user()
 if not u:return redirect(url_for("login"))
 return render_template("settings.html",user=u)
@app.route("/invite")
def invite():
 u=current_user()
 if not u:return redirect(url_for("login"))
 return render_template("invite.html",user=u)
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
