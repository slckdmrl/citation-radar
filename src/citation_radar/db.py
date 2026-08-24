from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Citation, Work


class Database:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def close(self) -> None:
        self.conn.close()

    def _migrate(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS works (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                doi TEXT,
                year INTEGER,
                url TEXT,
                tracked INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS citations (
                source_work_id TEXT NOT NULL,
                citing_work_id TEXT NOT NULL,
                citing_title TEXT NOT NULL,
                citing_year INTEGER,
                citing_doi TEXT,
                citing_url TEXT,
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_work_id, citing_work_id),
                FOREIGN KEY (source_work_id) REFERENCES works(id)
            );
            """
        )
        self.conn.commit()

    def upsert_work(self, work: Work) -> None:
        self.conn.execute(
            """
            INSERT INTO works(id, title, doi, year, url, tracked)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                doi=excluded.doi,
                year=excluded.year,
                url=excluded.url,
                tracked=1
            """,
            (work.id, work.title, work.doi, work.year, work.url),
        )
        self.conn.commit()

    def list_tracked_works(self) -> list[Work]:
        rows = self.conn.execute(
            "SELECT id, title, doi, year, url FROM works WHERE tracked=1 ORDER BY year DESC, title"
        ).fetchall()
        return [Work(*row) for row in rows]

    def add_citation_if_new(self, citation: Citation) -> bool:
        cur = self.conn.execute(
            """
            INSERT OR IGNORE INTO citations(
                source_work_id, citing_work_id, citing_title, citing_year, citing_doi, citing_url
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                citation.source_work_id,
                citation.citing_work_id,
                citation.citing_title,
                citation.citing_year,
                citation.citing_doi,
                citation.citing_url,
            ),
        )
        self.conn.commit()
        return cur.rowcount == 1
