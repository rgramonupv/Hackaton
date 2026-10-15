"""SQLite storage for residents, proposals and votes (one vote per resident and proposal)."""

import hashlib
import hmac
import json
from datetime import datetime
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
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER, dni TEXT, name TEXT, text TEXT,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    # Lightweight migrations for databases created by earlier versions.
    _add_column(conn, "votes", "value", "INTEGER DEFAULT 1")
    _add_column(conn, "proposals", "author_dni", "TEXT")
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for dni, name, barrio, pin in DEMO_USERS:
            _insert_user(conn, dni, name, barrio, pin)
    return conn


def _add_column(conn, table: str, column: str, decl: str) -> None:
    if column not in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


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


def save_proposal(barrio, title, author, benches, trees, cost, before, after, params, author_dni=None) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO proposals (barrio, title, author, benches, trees, cost, elderly_before, elderly_after,"
            " params, author_dni) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (barrio, title, author, json.dumps(benches), json.dumps(trees), cost, before, after, json.dumps(params),
             author_dni),
        )
        return cur.lastrowid


def _same_barrio(conn, proposal_id: int, dni: str) -> bool:
    user = conn.execute("SELECT barrio FROM users WHERE dni = ?", (dni,)).fetchone()
    prop = conn.execute("SELECT barrio FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
    return bool(user and prop and user["barrio"] == prop["barrio"])


def vote(proposal_id: int, dni: str, value: int = 1) -> str:
    """Vote for (+1) or against (-1). One vote per resident and proposal; voting again changes it.

    Returns "ok", "changed", "duplicate" or "wrong_barrio" (only residents of the proposal's barrio vote)."""
    with _conn() as conn:
        if not _same_barrio(conn, proposal_id, dni):
            return "wrong_barrio"
        old = conn.execute("SELECT value FROM votes WHERE proposal_id = ? AND voter = ?", (proposal_id, dni)).fetchone()
        if old and old["value"] == value:
            return "duplicate"
        conn.execute("INSERT INTO votes (proposal_id, voter, value) VALUES (?, ?, ?)"
                     " ON CONFLICT (proposal_id, voter) DO UPDATE SET value = excluded.value", (proposal_id, dni, value))
        return "changed" if old else "ok"


def my_vote(proposal_id: int, dni: str) -> int | None:
    with _conn() as conn:
        row = conn.execute("SELECT value FROM votes WHERE proposal_id = ? AND voter = ?", (proposal_id, dni)).fetchone()
    return row["value"] if row else None


def add_suggestion(proposal_id: int, dni: str, name: str, text: str) -> str:
    """Store an improvement suggestion (any registered resident, from any barrio)."""
    text = text.strip()
    if not text:
        return "empty"
    with _conn() as conn:
        conn.execute("INSERT INTO suggestions (proposal_id, dni, name, text, created) VALUES (?, ?, ?, ?, ?)",
                     (proposal_id, dni, name, text, datetime.now().strftime("%Y-%m-%d %H:%M")))
    return "ok"


def suggestions(proposal_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM suggestions WHERE proposal_id = ? ORDER BY id DESC", (proposal_id,))
        return [dict(r) for r in rows.fetchall()]


def ranking(barrio: str | None = None) -> list[dict]:
    """Proposals with votes for/against, net score and number of suggestions, best first."""
    query = (
        "SELECT p.*,"
        " COALESCE(SUM(CASE WHEN v.value = 1 THEN 1 END), 0) AS votes_for,"
        " COALESCE(SUM(CASE WHEN v.value = -1 THEN 1 END), 0) AS votes_against,"
        " (SELECT COUNT(*) FROM suggestions s WHERE s.proposal_id = p.id) AS n_suggestions"
        " FROM proposals p"
        " LEFT JOIN votes v ON v.proposal_id = p.id AND v.voter IN (SELECT dni FROM users)"
        + (" WHERE p.barrio = ?" if barrio else "")
        + " GROUP BY p.id ORDER BY votes_for - votes_against DESC, votes_for DESC, p.id"
    )
    with _conn() as conn:
        rows = conn.execute(query, (barrio,) if barrio else ()).fetchall()
    return [{**dict(r), "votes": r["votes_for"] - r["votes_against"]} for r in rows]
