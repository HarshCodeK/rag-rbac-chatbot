import sqlite3
import os

DB_PATH = "query_logs.db"


def _get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _get_connection()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            role TEXT,
            query TEXT,
            answer TEXT,
            blocked INTEGER,
            reason TEXT,
            latency_ms REAL
        )"""
    )
    conn.commit()
    conn.close()


def log_interaction(role, query, answer, blocked, reason, latency_ms):
    from datetime import datetime

    conn = _get_connection()
    conn.execute(
        "INSERT INTO logs (timestamp, role, query, answer, blocked, reason, latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), role, query, answer, int(blocked), reason, latency_ms),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit=20):
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT timestamp, role, query, answer, blocked, reason, latency_ms FROM logs ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


init_db()
