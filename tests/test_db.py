from pathlib import Path

from citation_radar.db import Database
from citation_radar.models import Citation, Work


def test_citation_notifications_are_globally_deduplicated(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    try:
        db.upsert_work(Work("W1", "Tracked paper 1", None, 2024, None))
        db.upsert_work(Work("W2", "Tracked paper 2", None, 2024, None))

        first = Citation("W1", "C1", "Citing paper", 2026, None, None)
        second = Citation("W2", "C1", "Citing paper", 2026, None, None)

        first_record = db.record_citation(first)
        assert first_record.is_new_global is True
        assert first_record.needs_notification is True

        db.mark_citing_work_notified("C1")

        second_record = db.record_citation(second)
        assert second_record.is_new_global is False
        assert second_record.needs_notification is False
    finally:
        db.close()


def test_unnotified_citations_stay_pending_for_retry(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    try:
        db.upsert_work(Work("W1", "Tracked paper", None, 2024, None))
        citation = Citation("W1", "C1", "Citing paper", 2026, None, None)

        first_record = db.record_citation(citation)
        second_record = db.record_citation(citation)

        assert first_record.is_new_global is True
        assert first_record.needs_notification is True
        assert second_record.is_new_global is False
        assert second_record.needs_notification is True
    finally:
        db.close()


def test_baseline_marks_existing_citations_as_notified(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    try:
        db.upsert_work(Work("W1", "Tracked paper", None, 2024, None))
        citation = Citation("W1", "C1", "Citing paper", 2026, None, None)

        baseline_record = db.record_citation(citation, baseline=True)
        follow_up_record = db.record_citation(citation)

        assert baseline_record.is_new_global is True
        assert baseline_record.needs_notification is False
        assert follow_up_record.is_new_global is False
        assert follow_up_record.needs_notification is False
    finally:
        db.close()
