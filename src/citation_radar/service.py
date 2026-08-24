from __future__ import annotations

from dataclasses import dataclass

from .db import Database
from .notifier import TelegramNotifier
from .openalex import OpenAlexClient


@dataclass(frozen=True)
class CheckResult:
    works_checked: int
    citations_seen: int
    new_citations: int
    notifications_sent: int


def sync_author_works(db: Database, client: OpenAlexClient, author_id: str) -> int:
    count = 0
    for work in client.iter_author_works(author_id):
        db.upsert_work(work)
        count += 1
    return count


def check_citations(
    db: Database,
    client: OpenAlexClient,
    notifier: TelegramNotifier | None,
    baseline: bool = False,
) -> CheckResult:
    works = db.list_tracked_works()
    seen = new = sent = 0

    for work in works:
        for citation in client.iter_citations(work):
            seen += 1
            record = db.record_citation(citation, baseline=baseline)
            if record.is_new_global:
                new += 1
            if not baseline and notifier is not None and record.needs_notification:
                notifier.send_new_citation(work, citation)
                db.mark_citing_work_notified(citation.citing_work_id)
                sent += 1

    return CheckResult(len(works), seen, new, sent)
