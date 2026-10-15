"""SQLite storage for residents, proposals and votes (one vote per resident and proposal)."""

import hashlib
import hmac
import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "valencia_futura.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barrio TEXT, title TEXT, author TEXT,
            benches TEXT, trees TEXT, cost REAL,
            elderly_before REAL, elderly_after REAL, params TEXT,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            dni TEXT PRIMARY KEY, name TEXT, barrio TEXT, salt BLOB, pin_hash BLOB
        );
        CREATE TABLE IF NOT EXISTS votes (
            proposal_id INTEGER, voter TEXT,
            PRIMARY KEY (proposal_id, voter)
        );
        """
    )
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for dni, name, barrio, pin in DEMO_USERS:
            _insert_user(conn, dni, name, barrio, pin)
    return conn


# DEMO: fictitious residents standing in for the municipal census (padrón).
DEMO_USERS = [
    ("11111111H", "Ana", "RUSSAFA", "1234"),
    ("22222222J", "Luis", "RUSSAFA", "1234"),
    ("33333333P", "Marta", "RUSSAFA", "1234"),
    ("44444444A", "Pepe", "BENICALAP", "1234"),
]


def _hash_pin(pin: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)


def _insert_user(conn, dni, name, barrio, pin) -> None:
    salt = os.urandom(16)
    conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (dni.upper(), name, barrio, salt, _hash_pin(pin, salt)))


def authenticate(dni: str, pin: str) -> dict | None:
    """Return {dni, name, barrio} if the DNI and PIN match a registered resident."""
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE dni = ?", (dni.strip().upper(),)).fetchone()
    if row and hmac.compare_digest(_hash_pin(pin, row["salt"]), row["pin_hash"]):
        return {"dni": row["dni"], "name": row["name"], "barrio": row["barrio"]}
    return None


def save_proposal(barrio, title, author, benches, trees, cost, before, after, params) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO proposals (barrio, title, author, benches, trees, cost, elderly_before, elderly_after, params)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (barrio, title, author, json.dumps(benches), json.dumps(trees), cost, before, after, json.dumps(params)),
        )
        return cur.lastrowid


def vote(proposal_id: int, dni: str) -> str:
    """Register a vote. Returns "ok", "duplicate" or "wrong_barrio" (only residents of the proposal's barrio vote)."""
    with _conn() as conn:
        user = conn.execute("SELECT barrio FROM users WHERE dni = ?", (dni,)).fetchone()
        prop = conn.execute("SELECT barrio FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        if not user or not prop or user["barrio"] != prop["barrio"]:
            return "wrong_barrio"
        cur = conn.execute("INSERT OR IGNORE INTO votes VALUES (?, ?)", (proposal_id, dni))
        return "ok" if cur.rowcount == 1 else "duplicate"


def ranking(barrio: str | None = None) -> list[dict]:
    query = (
        "SELECT p.*, COUNT(v.voter) AS votes FROM proposals p"
        " LEFT JOIN votes v ON v.proposal_id = p.id AND v.voter IN (SELECT dni FROM users)"
        + (" WHERE p.barrio = ?" if barrio else "")
        + " GROUP BY p.id ORDER BY votes DESC, p.id"
    )
    with _conn() as conn:
        rows = conn.execute(query, (barrio,) if barrio else ()).fetchall()
    return [dict(r) for r in rows]
