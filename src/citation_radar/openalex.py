from __future__ import annotations

from typing import Iterable

import httpx

from .models import Citation, Work

BASE_URL = "https://api.openalex.org"


def _short_id(value: str) -> str:
    return value.rsplit("/", 1)[-1]


class OpenAlexClient:
    def __init__(self, email: str | None = None, timeout: float = 30.0):
        self.params = {"mailto": email} if email else {}
        self.client = httpx.Client(timeout=timeout, headers={"User-Agent": "citation-radar/0.1"})

    def close(self) -> None:
        self.client.close()

    def _get(self, path: str, params: dict | None = None) -> dict:
        merged = dict(self.params)
        if params:
            merged.update(params)
        response = self.client.get(f"{BASE_URL}{path}", params=merged)
        response.raise_for_status()
        return response.json()

    def search_authors(self, name: str, per_page: int = 10) -> list[dict]:
        data = self._get("/authors", {"search": name, "per-page": per_page})
        return data.get("results", [])

    def iter_author_works(self, author_id: str) -> Iterable[Work]:
        cursor = "*"
        author_id = _short_id(author_id)
        while cursor:
            data = self._get(
                "/works",
                {
                    "filter": f"authorships.author.id:{author_id}",
                    "per-page": 200,
                    "cursor": cursor,
                    "select": "id,title,doi,publication_year,primary_location",
                },
            )
            for item in data.get("results", []):
                primary = item.get("primary_location") or {}
                yield Work(
                    id=_short_id(item["id"]),
                    title=item.get("title") or "(untitled)",
                    doi=item.get("doi"),
                    year=item.get("publication_year"),
                    url=primary.get("landing_page_url") or item.get("doi"),
                )
            cursor = (data.get("meta") or {}).get("next_cursor")

    def iter_citations(self, work: Work) -> Iterable[Citation]:
        cursor = "*"
        while cursor:
            data = self._get(
                "/works",
                {
                    "filter": f"cites:{_short_id(work.id)}",
                    "per-page": 200,
                    "cursor": cursor,
                    "select": "id,title,doi,publication_year,primary_location",
                },
            )
            for item in data.get("results", []):
                primary = item.get("primary_location") or {}
                yield Citation(
                    source_work_id=work.id,
                    citing_work_id=_short_id(item["id"]),
                    citing_title=item.get("title") or "(untitled)",
                    citing_year=item.get("publication_year"),
                    citing_doi=item.get("doi"),
                    citing_url=primary.get("landing_page_url") or item.get("doi"),
                )
            cursor = (data.get("meta") or {}).get("next_cursor")
