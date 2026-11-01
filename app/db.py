"""Database layer: raw, hand-written SQL on top of the stdlib sqlite3 module."""
import sqlite3
from pathlib import Path

from .seed_data import CANDIDATES, JOBS

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(path: str = "recruiter_bot.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())
    return conn


def _skill_id(conn: sqlite3.Connection, name: str) -> int:
    conn.execute("INSERT OR IGNORE INTO skills (name) VALUES (?)", (name,))
    return conn.execute("SELECT id FROM skills WHERE name = ?", (name,)).fetchone()["id"]


def seed(conn: sqlite3.Connection) -> dict:
    """Idempotent: wipes candidate/job data and reloads the seed set."""
    with conn:
        for table in ("candidate_skills", "candidate_traits", "job_skills",
                      "job_culture", "candidates", "jobs", "skills"):
            conn.execute(f"DELETE FROM {table}")  # table names are constants above

        for name, skills, exp, avail, traits, quirk in CANDIDATES:
            cur = conn.execute(
                "INSERT INTO candidates (name, experience_years, availability, quirk) VALUES (?, ?, ?, ?)",
                (name, exp, avail, quirk))
            cid = cur.lastrowid
            for s in skills:
                conn.execute("INSERT INTO candidate_skills (candidate_id, skill_id) VALUES (?, ?)",
                             (cid, _skill_id(conn, s)))
            for t in traits:
                conn.execute("INSERT INTO candidate_traits (candidate_id, trait) VALUES (?, ?)", (cid, t))

        for title, skills, min_exp, culture, tagline in JOBS:
            cur = conn.execute(
                "INSERT INTO jobs (title, min_experience, tagline) VALUES (?, ?, ?)",
                (title, min_exp, tagline))
            jid = cur.lastrowid
            for s in skills:
                conn.execute("INSERT INTO job_skills (job_id, skill_id) VALUES (?, ?)",
                             (jid, _skill_id(conn, s)))
            for k in culture:
                conn.execute("INSERT INTO job_culture (job_id, keyword) VALUES (?, ?)", (jid, k))
    return {"candidates": len(CANDIDATES), "jobs": len(JOBS)}


def is_empty(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) AS n FROM candidates").fetchone()["n"] == 0
