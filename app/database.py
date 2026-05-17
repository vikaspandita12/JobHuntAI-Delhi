import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = Path("data/jobs.db")


class Database:
    def init(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id       TEXT PRIMARY KEY,
                    title        TEXT,
                    company      TEXT,
                    location     TEXT,
                    source       TEXT,
                    url          TEXT,
                    description  TEXT,
                    salary       TEXT,
                    posted_date  TEXT,
                    vikas_score  INTEGER DEFAULT 0,
                    diksha_score INTEGER DEFAULT 0,
                    primary_profile TEXT DEFAULT 'vikas',
                    status       TEXT DEFAULT 'new',
                    created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                    notes        TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vikas  ON jobs(vikas_score DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_diksha ON jobs(diksha_score DESC)")

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def save_job(self, job: Dict):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO jobs
                    (job_id, title, company, location, source, url,
                     description, salary, posted_date,
                     vikas_score, diksha_score, primary_profile, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'new')
            """, (
                job.get("job_id"), job.get("title"), job.get("company"),
                job.get("location"), job.get("source"), job.get("url"),
                job.get("description", "")[:2000], job.get("salary", "Not disclosed"),
                job.get("posted_date", ""),
                job.get("vikas_score", 0), job.get("diksha_score", 0),
                job.get("primary_profile", "vikas")
            ))

    def job_exists(self, job_id: str) -> bool:
        with self._conn() as conn:
            return bool(conn.execute(
                "SELECT 1 FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone())

    def get_jobs(
        self,
        profile: Optional[str] = None,
        status: Optional[str] = None,
        min_score: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        clauses = ["1=1"]
        params: list = []

        if status:
            clauses.append("status = ?")
            params.append(status)

        if profile == "vikas":
            clauses.append("vikas_score >= ?")
            params.append(min_score)
            order = "vikas_score DESC"
        elif profile == "diksha":
            clauses.append("diksha_score >= ?")
            params.append(min_score)
            order = "diksha_score DESC"
        else:
            order = "MAX(vikas_score, diksha_score) DESC"

        params.append(limit)
        sql = f"SELECT * FROM jobs WHERE {' AND '.join(clauses)} ORDER BY {order} LIMIT ?"
        with self._conn() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_job_status(self, job_id: str, status: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status = ? WHERE job_id = ?",
                (status, job_id)
            )

    def update_notes(self, job_id: str, notes: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET notes = ? WHERE job_id = ?",
                (notes, job_id)
            )

    def get_stats(self) -> Dict:
        with self._conn() as conn:
            def count(sql, *args):
                return conn.execute(sql, args).fetchone()[0]
            return {
                "total":          count("SELECT COUNT(*) FROM jobs"),
                "new":            count("SELECT COUNT(*) FROM jobs WHERE status='new'"),
                "applied":        count("SELECT COUNT(*) FROM jobs WHERE status='applied'"),
                "skipped":        count("SELECT COUNT(*) FROM jobs WHERE status='skipped'"),
                "vikas_matches":  count("SELECT COUNT(*) FROM jobs WHERE vikas_score >= 60"),
                "diksha_matches": count("SELECT COUNT(*) FROM jobs WHERE diksha_score >= 50"),
                "sources":        {
                    r["source"]: r["cnt"]
                    for r in conn.execute(
                        "SELECT source, COUNT(*) cnt FROM jobs GROUP BY source"
                    ).fetchall()
                }
            }
