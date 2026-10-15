"""SQLite storage for proposals and votes (one vote per neighbour and proposal)."""

import json
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
        CREATE TABLE IF NOT EXISTS votes (
            proposal_id INTEGER, voter TEXT,
            PRIMARY KEY (proposal_id, voter)
        );
        """
    )
    return conn


def save_proposal(barrio, title, author, benches, trees, cost, before, after, params) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO proposals (barrio, title, author, benches, trees, cost, elderly_before, elderly_after, params)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (barrio, title, author, json.dumps(benches), json.dumps(trees), cost, before, after, json.dumps(params)),
        )
        return cur.lastrowid


def vote(proposal_id: int, voter: str) -> bool:
    """Register a vote; returns False if this voter already voted for it."""
    with _conn() as conn:
        cur = conn.execute("INSERT OR IGNORE INTO votes VALUES (?, ?)", (proposal_id, voter))
        return cur.rowcount == 1


def ranking(barrio: str | None = None) -> list[dict]:
    query = (
        "SELECT p.*, COUNT(v.voter) AS votes FROM proposals p"
        " LEFT JOIN votes v ON v.proposal_id = p.id"
        + (" WHERE p.barrio = ?" if barrio else "")
        + " GROUP BY p.id ORDER BY votes DESC, p.id"
    )
    with _conn() as conn:
        rows = conn.execute(query, (barrio,) if barrio else ()).fetchall()
    return [dict(r) for r in rows]
