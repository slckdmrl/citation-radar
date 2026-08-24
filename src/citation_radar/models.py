from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Work:
    id: str
    title: str
    doi: str | None
    year: int | None
    url: str | None


@dataclass(frozen=True)
class Citation:
    source_work_id: str
    citing_work_id: str
    citing_title: str
    citing_year: int | None
    citing_doi: str | None
    citing_url: str | None
