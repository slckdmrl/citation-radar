from pathlib import Path

from citation_radar.db import Database
from citation_radar.models import Citation, Work


def test_citation_deduplication(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    try:
        work = Work("W1", "Tracked paper", None, 2024, None)
        db.upsert_work(work)
        citation = Citation("W1", "W2", "Citing paper", 2026, None, None)
        assert db.add_citation_if_new(citation) is True
        assert db.add_citation_if_new(citation) is False
    finally:
        db.close()
