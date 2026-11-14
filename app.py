"""Backend for Kamya Sahoo's portfolio (Flask + SQLite).

Features
  POST /api/contact   validate + store a contact-form message (rate limited)
  GET  /api/messages  list stored messages (needs ADMIN_TOKEN)
  GET  /api/visit     count unique-per-session page visits, returns total
Run:  pip install -r requirements.txt && python app.py
"""
import os
import re
import sqlite3
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, abort

BASE = Path(__file__).parent
DB_PATH = os.environ.get("DB_PATH", str(BASE / "portfolio.db"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")  # set this to enable /api/messages
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RATE_LIMIT = 3          # messages
RATE_WINDOW = 600       # per 10 minutes, per IP

app = Flask(__name__, static_folder=None)
_hits = {}  # ip -> [timestamps]


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        c.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
        c.execute("INSERT OR IGNORE INTO stats VALUES ('visits', 0)")


def rate_limited(ip):
    now = time.time()
    recent = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW]
    if len(recent) >= RATE_LIMIT:
        _hits[ip] = recent
        return True
    recent.append(now)
    _hits[ip] = recent
    return False


@app.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or {}
    if data.get("website"):  # honeypot: bots fill hidden field
        return jsonify(ok=True)
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    message = str(data.get("message", "")).strip()
    errors = {}
    if not 1 <= len(name) <= 100:
        errors["name"] = "Please enter your name (max 100 characters)."
    if not EMAIL_RE.match(email) or len(email) > 254:
        errors["email"] = "Please enter a valid email address."
    if not 10 <= len(message) <= 2000:
        errors["message"] = "Message must be 10 to 2000 characters."
    if errors:
        return jsonify(ok=False, errors=errors), 400
    if rate_limited(request.remote_addr or "unknown"):
        return jsonify(ok=False, error="Too many messages. Please try again later."), 429
    with db() as c:
        c.execute("INSERT INTO messages (name, email, message) VALUES (?,?,?)", (name, email, message))
    return jsonify(ok=True), 201


@app.get("/api/messages")
def messages():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        abort(401)
    with db() as c:
        rows = c.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/visit")
def visit():
    with db() as c:
        if request.args.get("count") == "1":
            c.execute("UPDATE stats SET value = value + 1 WHERE key='visits'")
        total = c.execute("SELECT value FROM stats WHERE key='visits'").fetchone()[0]
    return jsonify(visits=total)


# ---- static site ----
ALLOWED = {"index.html", "style.css", "script.js"}


@app.get("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.get("/<path:path>")
def static_files(path):
    if path in ALLOWED or path.startswith("assets/"):
        return send_from_directory(BASE, path)
    abort(404)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
