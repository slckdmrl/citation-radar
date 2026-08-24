from pathlib import Path

import pytest

from citation_radar.db import Database
from citation_radar.models import Citation, Work
from citation_radar.notifier import NotificationError
from citation_radar.service import check_citations


class StaticClient:
    def __init__(self, works: list[Work], citations_by_work: dict[str, list[Citation]]):
        self._works = works
        self._citations_by_work = citations_by_work

    def iter_author_works(self, author_id: str):
        return iter(self._works)

    def iter_citations(self, work: Work):
        return iter(self._citations_by_work.get(work.id, []))


class FlakyNotifier:
    def __init__(self):
        self.calls = 0

    def send_new_citation(self, source: Work, citation: Citation) -> None:
        self.calls += 1
        if self.calls == 1:
            raise NotificationError("temporary failure")


def test_failed_notifications_are_retried_on_next_run(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    try:
        work = Work("W1", "Tracked paper", None, 2024, None)
        db.upsert_work(work)
        citation = Citation("W1", "C1", "Citing paper", 2026, None, None)
        client = StaticClient([work], {"W1": [citation]})
        notifier = FlakyNotifier()

        with pytest.raises(NotificationError, match="temporary failure"):
            check_citations(db, client, notifier, baseline=False)

        result = check_citations(db, client, notifier, baseline=False)

        assert result.new_citations == 0
        assert result.notifications_sent == 1
        assert notifier.calls == 2
    finally:
        db.close()
