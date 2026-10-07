import sqlite3
from contextlib import contextmanager
from datetime import datetime

import config


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                hostname TEXT NOT NULL,
                port INTEGER NOT NULL DEFAULT 443,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                checked_at TEXT NOT NULL,
                days_remaining INTEGER,
                expiry_date TEXT,
                issuer TEXT,
                status TEXT,
                error TEXT,
                FOREIGN KEY(site_id) REFERENCES sites(id) ON DELETE CASCADE
            )
        """)


def add_site(label, hostname, port=443):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sites (label, hostname, port, active, created_at) VALUES (?, ?, ?, 1, ?)",
            (label, hostname, port, datetime.utcnow().isoformat()),
        )


def delete_site(site_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM checks WHERE site_id = ?", (site_id,))
        conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))


def toggle_site(site_id, active):
    with get_conn() as conn:
        conn.execute("UPDATE sites SET active = ? WHERE id = ?", (1 if active else 0, site_id))


def list_sites(only_active=False):
    with get_conn() as conn:
        q = "SELECT * FROM sites"
        if only_active:
            q += " WHERE active = 1"
        q += " ORDER BY label"
        return [dict(r) for r in conn.execute(q).fetchall()]


def save_check_result(site_id, result):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO checks (site_id, checked_at, days_remaining, expiry_date, issuer, status, error)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                site_id,
                datetime.utcnow().isoformat(),
                result.get("days_remaining"),
                result.get("expiry_date"),
                result.get("issuer"),
                result.get("status"),
                result.get("error"),
            ),
        )


def get_last_result_per_site():
    """Devuelve el ultimo chequeo guardado para cada sitio activo."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT s.*, c.checked_at, c.days_remaining, c.expiry_date, c.issuer, c.status, c.error
            FROM sites s
            LEFT JOIN checks c ON c.id = (
                SELECT id FROM checks WHERE site_id = s.id ORDER BY checked_at DESC LIMIT 1
            )
            ORDER BY s.label
        """).fetchall()
        return [dict(r) for r in rows]
