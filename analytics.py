"""Tracking des posts generés et publies — SQLite local."""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            discipline TEXT,
            source TEXT,
            accroche TEXT,
            instagram_url TEXT,
            triggered_by TEXT DEFAULT 'manual'
        )
    """)
    c.commit()
    return c


def log_post(discipline: str, source: str, accroche: str,
             instagram_url: str = "", triggered_by: str = "manual"):
    c = _conn()
    c.execute(
        "INSERT INTO posts (ts, discipline, source, accroche, instagram_url, triggered_by) VALUES (?,?,?,?,?,?)",
        (datetime.utcnow().isoformat(), discipline, source, accroche[:80],
         instagram_url, triggered_by)
    )
    c.commit()
    c.close()


def weekly_report() -> str:
    c = _conn()
    since = (datetime.utcnow() - timedelta(days=7)).isoformat()
    rows = c.execute(
        "SELECT discipline, source, triggered_by, COUNT(*) as n FROM posts "
        "WHERE ts >= ? GROUP BY discipline, source, triggered_by ORDER BY n DESC",
        (since,)
    ).fetchall()
    total = c.execute("SELECT COUNT(*) FROM posts WHERE ts >= ?", (since,)).fetchone()[0]
    insta = c.execute(
        "SELECT COUNT(*) FROM posts WHERE ts >= ? AND instagram_url != ''", (since,)
    ).fetchone()[0]
    c.close()

    if total == 0:
        return "Aucun post cette semaine."

    lines = [f"Rapport 7 jours — {total} posts generes, {insta} publies sur Instagram\n"]
    for disc, src, trig, n in rows:
        lines.append(f"  {disc or '?'} via {src} ({trig}) : {n}x")
    return "\n".join(lines)


def total_posts() -> int:
    c = _conn()
    n = c.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    c.close()
    return n
