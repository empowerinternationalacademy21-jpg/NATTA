# ✦ Chom — Unfiltered  (Flask Edition)

The full-featured personal blog — now with a real Python backend.

## Quick Start

```bash
# Install Flask (once)
pip install flask

# Run
python3 start.py

# Open → http://localhost:5000
```

## Admin
Click the **key icon** (🔑) in the top-right of the blog, or the nav.  
- **Username:** `chom123`  
- **Password:** `godislove1234`

## What changed vs. the original HTML

| Before | After |
|--------|-------|
| JSONbin.io cloud API | Flask + SQLite (local, permanent) |
| Posts lost on tab close | Posts saved to `chom.db` forever |
| Views tracked by localStorage | Views tracked **server-side** (no faking) |
| Likes/upvotes reset per-browser | Likes/upvotes synced to all visitors |
| Needed internet for data | Works fully **offline** |
| Setup required external account | Zero config — just `python3 start.py` |

## View Deduplication
- **User A** opens post → 1 view
- **User A** opens again → still 1 view (server deduplicates by session + IP + browser)
- **User B** opens post → 2 views
- Both users see the same live count instantly

## Files
```
app.py              ← Flask backend (all routes, SQLite logic)
start.py            ← Run this to start the blog
templates/
  index.html        ← The full blog UI (original design, ~3000 lines)
static/
  uploads/          ← Media uploaded via the admin panel
chom.db             ← SQLite database (auto-created on first run)
```

## API Endpoints
| Method | Route | Purpose |
|--------|-------|---------|
| `GET` | `/api/data` | Load all posts, theme, meta |
| `PUT` | `/api/data` | Save posts/theme/photoTheme |
| `POST` | `/api/view/:id` | Record unique view (server-side) |
| `POST` | `/api/login` | Admin login → session cookie |
| `POST` | `/api/logout` | Admin logout |
| `GET` | `/api/admin-status` | Check if admin is logged in |

---
*"The life I show isn't the life I live — and that's okay."*
