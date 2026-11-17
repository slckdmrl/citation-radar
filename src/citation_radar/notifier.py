from __future__ import annotations

import html
from urllib.parse import urlparse

import httpx

from .models import Citation, Work
from .openalex import OpenAlexClient, OpenAlexError


class NotificationError(RuntimeError):
    pass


class TelegramNotifier:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        timeout: float = 20.0,
        compare_sources: tuple[str, ...] = (),
        google_scholar_profile_url: str | None = None,
        researchgate_profile_url: str | None = None,
        totals_client: OpenAlexClient | None = None,
        author_id: str | None = None,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout
        self.compare_sources = compare_sources
        self.google_scholar_profile_url = google_scholar_profile_url
        self.researchgate_profile_url = researchgate_profile_url
        self.totals_client = totals_client
        self.author_id = author_id
        self._totals: dict[tuple[str, str], int | None] = {}

    def _total(self, entity: str, entity_id: str | None) -> int | None:
        if self.totals_client is None or not entity_id:
            return None
        key = (entity, entity_id)
        if key not in self._totals:
            try:
                self._totals[key] = self.totals_client.citation_total(entity, entity_id)
            except OpenAlexError:
                self._totals[key] = None
        return self._totals[key]

    def send_new_citation(self, source: Work, citation: Citation) -> None:
        text = self._format_message(
            source,
            citation,
            compare_sources=self.compare_sources,
            google_scholar_profile_url=self.google_scholar_profile_url,
            researchgate_profile_url=self.researchgate_profile_url,
            work_total=self._total("works", source.id),
            author_total=self._total("authors", self.author_id),
        )
        try:
            response = httpx.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise NotificationError("Telegram request failed.") from exc

        if response.status_code >= 400:
            raise NotificationError(f"Telegram request failed with HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise NotificationError("Telegram returned invalid JSON.") from exc

        if not payload.get("ok", False):
            description = payload.get("description") or "Unknown Telegram error."
            raise NotificationError(f"Telegram API error: {description}")

    @staticmethod
    def _format_message(
        source: Work,
        citation: Citation,
        *,
        compare_sources: tuple[str, ...] = (),
        google_scholar_profile_url: str | None = None,
        researchgate_profile_url: str | None = None,
        work_total: int | None = None,
        author_total: int | None = None,
    ) -> str:
        source_title = html.escape(source.title)
        citing_title = html.escape(citation.citing_title)
        year = str(citation.citing_year) if citation.citing_year else "?"
        lines = [
            "🔔 <b>Yeni atıf bulundu</b>",
            "",
            f"<b>Atıf alan:</b> {source_title}",
            f"<b>Atıf yapan:</b> {citing_title}",
            f"<b>Yıl:</b> {year}",
        ]
        if citation.citing_doi:
            lines.append(f"<b>DOI:</b> {html.escape(citation.citing_doi)}")
        if work_total is not None:
            lines.append(f"<b>Makalenin toplam atfı (OpenAlex):</b> {work_total}")
        if author_total is not None:
            lines.append(f"<b>Araştırmacının toplam atfı (OpenAlex):</b> {author_total}")
        if citation.citing_url:
            safe_url = html.escape(citation.citing_url, quote=True)
            lines.append(f'<a href="{safe_url}">Çalışmayı aç</a>')

        compare_links = TelegramNotifier._build_compare_links(
            compare_sources,
            google_scholar_profile_url,
            researchgate_profile_url,
        )
        if compare_links:
            lines.append("")
            lines.append("<b>Çapraz kontrol:</b>")
            for label, url in compare_links:
                safe_url = html.escape(url, quote=True)
                lines.append(f'<a href="{safe_url}">{html.escape(label)}</a>')
        return "\n".join(lines)

    @staticmethod
    def _build_compare_links(
        compare_sources: tuple[str, ...],
        google_scholar_profile_url: str | None,
        researchgate_profile_url: str | None,
    ) -> list[tuple[str, str]]:
        links: list[tuple[str, str]] = []
        for source in compare_sources:
            if source == "google-scholar" and TelegramNotifier._is_http_url(google_scholar_profile_url):
                links.append(("Google Scholar profili", google_scholar_profile_url))
            elif source == "researchgate" and TelegramNotifier._is_http_url(researchgate_profile_url):
                links.append(("ResearchGate profili", researchgate_profile_url))
        return links

    @staticmethod
    def _is_http_url(value: str | None) -> bool:
        if not value:
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
