"""
╔══════════════════════════════════════════════════════╗
║   CHOM — UNFILTERED  ·  Flask Python Backend         ║
║                                                      ║
║   Start:   python3 app.py                            ║
║   URL:     http://localhost:5000                     ║
║   Admin:   click "Open Studio" on the blog           ║
║   Creds:   chom123  /  godislove1234                 ║
╚══════════════════════════════════════════════════════╝
"""
import os
import json
import sqlite3
import hashlib
import base64
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify,
    session, send_from_directory
)

# ─── Setup ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DB_PATH      = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'chom.db'))
UPLOAD_FOLDER= os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'chom_unfiltered_flask_secret_2025_xK7!rQ9'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

ADMIN_USER = 'chom123'
ADMIN_PASS = 'godislove1234'

# ─── Database ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables and seed default data if first run."""
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS blog_data (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_reactions (
            user_hash TEXT NOT NULL,
            post_id   TEXT NOT NULL,
            action    TEXT NOT NULL,  -- 'like','upvote','view'
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_hash, post_id, action)
        );
        """)
        # Seed initial blog state if not present
        if not db.execute("SELECT 1 FROM blog_data WHERE key='state'").fetchone():
            initial = {
                "posts": [
                    {
                        "id": 1735000000000,
                        "title": "Pretending Is Not Free",
                        "subtitle": "The cost of switching versions of yourself.",
                        "body": "I've learned how to switch versions of myself.\n\nThere's the version of me in the compound — laughing, fitting in, sounding like everything is fine. Then there's the version of me alone: counting every step, every thought, careful with plans, careful with money — counting it twice before spending it once — careful with what I even say.\n\nSchool taught me how to adjust, how to edit my life in real time... how to make ordinary things sound bigger and skip details when it's easier than explaining.\n\nBut pretending… pretending can hurt. It doesn't hit you, it *squeezes* you slowly. It makes you question if your real life is enough. It makes you feel small, like you have to shrink to fit in. And sometimes, you just feel exhausted.\n\nExhausted from performing in class.\nExhausted from stepping back into a completely different world after the bell rings.\n\nThat's when I realised — I don't want to suffocate just to fit. I don't want to hide pieces of myself.\n\nThe life I show isn't the life I live — and that's okay. I'm allowed to be messy, stressed, scared, and still matter. I'm allowed to exist in both worlds without pretending. I'm allowed to claim my space, my voice, my story.\n\n**And I'm done shrinking for anyone else.**",
                        "cat": "Truth",
                        "design": "d1",
                        "coverImg": None,
                        "coverType": "curated",
                        "media": [],
                        "videoUrl": None,
                        "slides": [],
                        "ssSpeed": 4000,
                        "ssLoop": True,
                        "ssFullHero": False,
                        "date": "2025-01-01T00:00:00.000Z"
                    }
                ],
                "theme": "ember",
                "photoTheme": {},
                "meta": {
                    "1735000000000": {
                        "likes": 0, "upvotes": 0, "views": 0,
                        "viewers": [], "comments": []
                    }
                }
            }
            db.execute(
                "INSERT INTO blog_data(key,value) VALUES('state',?)",
                (json.dumps(initial),)
            )
            db.commit()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_state():
    """Load the entire blog state from SQLite."""
    with get_db() as db:
        row = db.execute("SELECT value FROM blog_data WHERE key='state'").fetchone()
    if row:
        return json.loads(row['value'])
    return {"posts": [], "theme": "ember", "photoTheme": {}, "meta": {}}

def save_state(state):
    """Persist the entire blog state to SQLite."""
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO blog_data(key,value) VALUES('state',?)",
            (json.dumps(state),)
        )
        db.commit()

def user_fingerprint(req):
    """Create a stable per-user hash from IP + User-Agent + session ID."""
    if 'uid' not in session:
        session['uid'] = base64.b64encode(os.urandom(16)).decode()
    ip = req.headers.get('X-Forwarded-For', req.remote_addr) or '0.0.0.0'
    ua = req.headers.get('User-Agent', '')
    raw = f"{ip}|{ua}|{session['uid']}"
    return hashlib.sha256(raw.encode()).hexdigest()

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ── Blog Data API ─────────────────────────────────────────────────────────────
@app.route('/api/data', methods=['GET'])
def api_get_data():
    """Return the full blog state (posts, theme, photoTheme, meta)."""
    state = get_state()
    return jsonify(state)

@app.route('/api/data', methods=['PUT'])
def api_put_data():
    """
    Accept a full or partial state update from the JS frontend.
    The JS sends the entire _cloudData object on every save.
    We merge carefully to protect view/like counts.
    """
    incoming = request.get_json(force=True, silent=True)
    if not incoming:
        return jsonify({"ok": False, "error": "No JSON body"}), 400

    state = get_state()

    # Update safe fields
    if 'posts' in incoming:
        state['posts'] = incoming['posts']
    if 'theme' in incoming:
        state['theme'] = incoming['theme']
    if 'photoTheme' in incoming:
        state['photoTheme'] = incoming['photoTheme']
    if 'meta' in incoming:
        # Merge meta carefully — never let the frontend zero out server counts
        incoming_meta = incoming['meta']
        if not state.get('meta'):
            state['meta'] = {}
        for post_id, pm in incoming_meta.items():
            existing = state['meta'].get(post_id, {})
            # Likes and upvotes come from the frontend (toggle operations)
            # Views and viewers are managed server-side via /api/view
            # But we accept them from the frontend for the initial cloud-sync path
            merged = {
                'likes':    pm.get('likes',    existing.get('likes', 0)),
                'upvotes':  pm.get('upvotes',  existing.get('upvotes', 0)),
                'views':    max(pm.get('views', 0), existing.get('views', 0)),
                'viewers':  list(set(
                    existing.get('viewers', []) + pm.get('viewers', [])
                )),
                'comments': pm.get('comments', existing.get('comments', [])),
            }
            state['meta'][post_id] = merged

    save_state(state)
    return jsonify({"ok": True})

# ── View Tracking (server-authoritative) ──────────────────────────────────────
@app.route('/api/view/<post_id>', methods=['POST'])
def api_view(post_id):
    """
    Record a unique view for this post+user combination.
    Returns the current unique view count.
    """
    uhash = user_fingerprint(request)
    now   = datetime.now().isoformat()

    with get_db() as db:
        existing = db.execute(
            "SELECT 1 FROM user_reactions WHERE user_hash=? AND post_id=? AND action='view'",
            (uhash, post_id)
        ).fetchone()
        is_new = not existing
        if is_new:
            db.execute(
                "INSERT OR IGNORE INTO user_reactions(user_hash,post_id,action,created_at) VALUES(?,?,?,?)",
                (uhash, post_id, 'view', now)
            )
            db.commit()

    # Update the state meta
    state = get_state()
    if 'meta' not in state:
        state['meta'] = {}
    if post_id not in state['meta']:
        state['meta'][post_id] = {'likes': 0, 'upvotes': 0, 'views': 0, 'viewers': [], 'comments': []}

    if is_new and uhash not in state['meta'][post_id].get('viewers', []):
        state['meta'][post_id].setdefault('viewers', []).append(uhash)
        state['meta'][post_id]['views'] = len(state['meta'][post_id]['viewers'])
        save_state(state)

    return jsonify({
        "views":   state['meta'][post_id]['views'],
        "is_new":  is_new,
        "viewer_id": uhash
    })

# ── Admin Auth ────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(force=True, silent=True) or {}
    u = data.get('u', '').strip()
    p = data.get('p', '')
    if u == ADMIN_USER and p == ADMIN_PASS:
        session['admin'] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('admin', None)
    return jsonify({"ok": True})

@app.route('/api/admin-status')
def api_admin_status():
    return jsonify({"admin": bool(session.get('admin'))})

# ── Static uploads ────────────────────────────────────────────────────────────
@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("\n" + "═" * 56)
    print("  ✦  CHOM — UNFILTERED  ·  Flask backend ready")
    print("═" * 56)
    print(f"  Blog:    http://localhost:5000")
    print(f"  Login:   chom123  /  godislove1234")
    print("═" * 56 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Called by gunicorn — initialise DB on startup
    init_db()