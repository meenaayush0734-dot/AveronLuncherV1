import os, sqlite3, secrets, time
from functools import wraps
from flask import Flask, request, session, redirect, jsonify, render_template_string, abort
from werkzeug.security import check_password_hash

ADMIN_USER = os.environ.get("ADMIN_USER", "EliteShorter")
ADMIN_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
SECRET = os.environ.get("SECRET_KEY")
if not ADMIN_HASH or not SECRET:
    raise SystemExit("Set ADMIN_PASSWORD_HASH and SECRET_KEY env vars (see README).")

app = Flask(__name__)
app.secret_key = SECRET
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
DB = os.environ.get("DB_PATH", "averon.db")
fails = {}  # ip -> (count, first_time)

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS crashes(id INTEGER PRIMARY KEY, ts INT, version TEXT, device TEXT, log TEXT);
        CREATE TABLE IF NOT EXISTS downloads(id INTEGER PRIMARY KEY, ts INT, mc_version TEXT);
        CREATE TABLE IF NOT EXISTS profiles(id INTEGER PRIMARY KEY, ts INT, name TEXT UNIQUE, banned INT DEFAULT 0);
        CREATE TABLE IF NOT EXISTS disabled_versions(v TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
        """)
        for k, v in {"latest_version": "1.0.0", "min_version": "1.0.0", "update_url": "", "notice": ""}.items():
            c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, v))
init()

def cfg():
    with db() as c:
        return {r["k"]: r["v"] for r in c.execute("SELECT * FROM settings")}

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"): return redirect("/login")
        return f(*a, **k)
    return w

def csrf_ok():
    return request.form.get("csrf") and request.form.get("csrf") == session.get("csrf")

# ---------- public API for the launcher ----------
@app.get("/api/config")
def api_config():
    c = cfg()
    with db() as d:
        dis = [r["v"] for r in d.execute("SELECT v FROM disabled_versions")]
    return jsonify(latest_version=c["latest_version"], min_version=c["min_version"],
                   update_url=c["update_url"], notice=c["notice"], disabled_versions=dis)

@app.post("/api/crash")
def api_crash():
    j = request.get_json(silent=True) or {}
    with db() as c:
        c.execute("INSERT INTO crashes(ts,version,device,log) VALUES(?,?,?,?)",
                  (int(time.time()), str(j.get("version",""))[:40], str(j.get("device",""))[:80], str(j.get("log",""))[:20000]))
    return jsonify(ok=True)

@app.post("/api/download")
def api_download():
    j = request.get_json(silent=True) or {}
    with db() as c:
        c.execute("INSERT INTO downloads(ts,mc_version) VALUES(?,?)", (int(time.time()), str(j.get("mc_version",""))[:30]))
    return jsonify(ok=True)

@app.post("/api/profile")
def api_profile():
    j = request.get_json(silent=True) or {}
    name = str(j.get("name",""))[:32].strip()
    if not name: return jsonify(ok=False), 400
    with db() as c:
        c.execute("INSERT OR IGNORE INTO profiles(ts,name) VALUES(?,?)", (int(time.time()), name))
        banned = c.execute("SELECT banned FROM profiles WHERE name=?", (name,)).fetchone()["banned"]
    return jsonify(ok=True, banned=bool(banned))

# ---------- admin ----------
LOGIN = """<body style="background:#000;color:#f3e9ff;font-family:sans-serif;display:grid;place-items:center;height:100vh;margin:0">
<form method=post style="background:#120b1c;border:1px solid #7b2fff80;border-radius:16px;padding:28px;width:280px">
<h2 style="color:#b388ff;margin-top:0">AVERON Admin</h2>
<input name=u placeholder=Username style="width:100%;padding:10px;margin:6px 0;background:#000;color:#fff;border:1px solid #7b2fff80;border-radius:8px">
<input name=p type=password placeholder=Password style="width:100%;padding:10px;margin:6px 0;background:#000;color:#fff;border:1px solid #7b2fff80;border-radius:8px">
<button style="width:100%;padding:12px;margin-top:8px;border:0;border-radius:10px;color:#fff;font-weight:bold;background:linear-gradient(90deg,#4a148c,#7b2fff)">Login</button>
<p style="color:#ff8a9a">{{e}}</p></form></body>"""

@app.route("/login", methods=["GET", "POST"])
def login():
    ip = request.remote_addr; err = ""
    n, t = fails.get(ip, (0, time.time()))
    if time.time() - t > 600: n, t = 0, time.time()
    if n >= 5: return render_template_string(LOGIN, e="Too many attempts. Wait 10 min."), 429
    if request.method == "POST":
        ok = request.form.get("u") == ADMIN_USER and check_password_hash(ADMIN_HASH, request.form.get("p", ""))
        if ok:
            session.clear(); session["admin"] = True; session["csrf"] = secrets.token_hex(16)
            fails.pop(ip, None); return redirect("/")
        fails[ip] = (n + 1, t); err = "Wrong username or password"
    return render_template_string(LOGIN, e=err)

@app.get("/logout")
def logout():
    session.clear(); return redirect("/login")

DASH = """<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>AVERON Admin</title>
<style>
body{background:#000;color:#f3e9ff;font-family:sans-serif;margin:0;padding:14px}
h1,h2{color:#b388ff} .card{background:#120b1c;border:1px solid #7b2fff80;border-radius:16px;padding:14px;margin:12px 0}
input,textarea{background:#000;color:#fff;border:1px solid #7b2fff80;border-radius:8px;padding:8px;width:100%;box-sizing:border-box;margin:4px 0}
button{border:0;border-radius:10px;color:#fff;font-weight:bold;padding:10px 14px;background:linear-gradient(90deg,#4a148c,#7b2fff)}
pre{white-space:pre-wrap;word-break:break-all;color:#9e8fb5;max-height:160px;overflow:auto} a{color:#b388ff}
</style>
<h1>AVERON Admin <small style="font-size:12px"><a href=/logout>logout</a></small></h1>
<div class=card><h2>Stats</h2>Downloads: {{dl}} | Profiles: {{pc}} | Crashes: {{cc}}<br>
Top versions: {% for r in top %}{{r.mc_version}} ({{r.n}}) {% endfor %}</div>
<div class=card><h2>Update management</h2><form method=post action=/settings>
<input type=hidden name=csrf value="{{csrf}}">
Latest version<input name=latest_version value="{{c.latest_version}}">
Minimum version<input name=min_version value="{{c.min_version}}">
Update URL<input name=update_url value="{{c.update_url}}">
Notice (shown in launcher)<textarea name=notice>{{c.notice}}</textarea>
<button>Save</button></form></div>
<div class=card><h2>Disabled Minecraft versions</h2>
{% for v in dis %}<form method=post action=/version/enable style="display:inline"><input type=hidden name=csrf value="{{csrf}}"><input type=hidden name=v value="{{v}}"><button>{{v}} ✕</button></form> {% endfor %}
<form method=post action=/version/disable><input type=hidden name=csrf value="{{csrf}}"><input name=v placeholder="e.g. 1.20.1"><button>Disable</button></form></div>
<div class=card><h2>Profiles</h2>
{% for p in profiles %}<form method=post action=/profile/toggle style="margin:4px 0"><input type=hidden name=csrf value="{{csrf}}"><input type=hidden name=id value="{{p.id}}">
{{p.name}} {{'(BANNED)' if p.banned else ''}} <button>{{'Unban' if p.banned else 'Ban'}}</button></form>{% endfor %}</div>
<div class=card><h2>Crash reports</h2>
{% for r in crashes %}<div><b>{{r.version}}</b> {{r.device}}<pre>{{r.log}}</pre>
<form method=post action=/crash/delete><input type=hidden name=csrf value="{{csrf}}"><input type=hidden name=id value="{{r.id}}"><button>Delete</button></form></div><hr>{% endfor %}</div>
"""

@app.get("/")
@login_required
def dash():
    with db() as c:
        ctx = dict(
            dl=c.execute("SELECT COUNT(*) FROM downloads").fetchone()[0],
            pc=c.execute("SELECT COUNT(*) FROM profiles").fetchone()[0],
            cc=c.execute("SELECT COUNT(*) FROM crashes").fetchone()[0],
            top=c.execute("SELECT mc_version, COUNT(*) n FROM downloads GROUP BY mc_version ORDER BY n DESC LIMIT 5").fetchall(),
            dis=[r["v"] for r in c.execute("SELECT v FROM disabled_versions")],
            profiles=c.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 50").fetchall(),
            crashes=c.execute("SELECT * FROM crashes ORDER BY id DESC LIMIT 20").fetchall(),
            c=cfg(), csrf=session["csrf"])
    return render_template_string(DASH, **ctx)

def post_guard():
    if not session.get("admin") or not csrf_ok(): abort(403)

@app.post("/settings")
def settings():
    post_guard()
    with db() as c:
        for k in ("latest_version", "min_version", "update_url", "notice"):
            c.execute("REPLACE INTO settings VALUES(?,?)", (k, request.form.get(k, "")[:500]))
    return redirect("/")

@app.post("/version/disable")
def vdis():
    post_guard()
    v = request.form.get("v", "").strip()[:30]
    if v:
        with db() as c: c.execute("INSERT OR IGNORE INTO disabled_versions VALUES(?)", (v,))
    return redirect("/")

@app.post("/version/enable")
def ven():
    post_guard()
    with db() as c: c.execute("DELETE FROM disabled_versions WHERE v=?", (request.form.get("v", ""),))
    return redirect("/")

@app.post("/profile/toggle")
def ptoggle():
    post_guard()
    with db() as c: c.execute("UPDATE profiles SET banned=1-banned WHERE id=?", (request.form.get("id"),))
    return redirect("/")

@app.post("/crash/delete")
def cdel():
    post_guard()
    with db() as c: c.execute("DELETE FROM crashes WHERE id=?", (request.form.get("id"),))
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
