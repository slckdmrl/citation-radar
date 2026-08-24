from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .models import Citation, Work


@dataclass(frozen=True)
class CitationRecord:
    is_new_global: bool
    needs_notification: bool


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
                notified_at TEXT,
                PRIMARY KEY (source_work_id, citing_work_id),
                FOREIGN KEY (source_work_id) REFERENCES works(id)
            );

            CREATE INDEX IF NOT EXISTS idx_citations_citing_work_id
            ON citations(citing_work_id);
            """
        )
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(citations)").fetchall()}
        if "notified_at" not in columns:
            self.conn.execute("ALTER TABLE citations ADD COLUMN notified_at TEXT")
            self.conn.execute(
                """
                UPDATE citations
                SET notified_at = COALESCE(first_seen_at, CURRENT_TIMESTAMP)
                WHERE notified_at IS NULL
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

    def record_citation(self, citation: Citation, baseline: bool = False) -> CitationRecord:
        is_new_global = not self._citation_exists(citation.citing_work_id)
        already_notified = self._citation_is_notified(citation.citing_work_id)
        notified_at = "CURRENT_TIMESTAMP" if baseline or already_notified else "NULL"

        existing_relation = self.conn.execute(
            """
            SELECT 1
            FROM citations
            WHERE source_work_id = ? AND citing_work_id = ?
            """,
            (citation.source_work_id, citation.citing_work_id),
        ).fetchone()

        if existing_relation:
            self.conn.execute(
                f"""
                UPDATE citations
                SET citing_title = ?,
                    citing_year = ?,
                    citing_doi = ?,
                    citing_url = ?,
                    notified_at = COALESCE(notified_at, {notified_at})
                WHERE source_work_id = ? AND citing_work_id = ?
                """,
                (
                    citation.citing_title,
                    citation.citing_year,
                    citation.citing_doi,
                    citation.citing_url,
                    citation.source_work_id,
                    citation.citing_work_id,
                ),
            )
        else:
            self.conn.execute(
                f"""
                INSERT INTO citations(
                    source_work_id,
                    citing_work_id,
                    citing_title,
                    citing_year,
                    citing_doi,
                    citing_url,
                    notified_at
                ) VALUES (?, ?, ?, ?, ?, ?, {notified_at})
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

        if baseline:
            self.mark_citing_work_notified(citation.citing_work_id, commit=False)

        self.conn.commit()
        return CitationRecord(
            is_new_global=is_new_global,
            needs_notification=not baseline and not self._citation_is_notified(citation.citing_work_id),
        )

    def mark_citing_work_notified(self, citing_work_id: str, commit: bool = True) -> None:
        self.conn.execute(
            """
            UPDATE citations
            SET notified_at = COALESCE(notified_at, CURRENT_TIMESTAMP)
            WHERE citing_work_id = ?
            """,
            (citing_work_id,),
        )
        if commit:
            self.conn.commit()

    def _citation_exists(self, citing_work_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM citations WHERE citing_work_id = ? LIMIT 1",
            (citing_work_id,),
        ).fetchone()
        return row is not None

    def _citation_is_notified(self, citing_work_id: str) -> bool:
        row = self.conn.execute(
            """
            SELECT 1
            FROM citations
            WHERE citing_work_id = ? AND notified_at IS NOT NULL
            LIMIT 1
            """,
            (citing_work_id,),
        ).fetchone()
        return row is not None
