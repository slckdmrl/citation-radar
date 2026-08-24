from __future__ import annotations

import html

import httpx

from .models import Citation, Work


class NotificationError(RuntimeError):
    pass


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout: float = 20.0):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    def send_new_citation(self, source: Work, citation: Citation) -> None:
        text = self._format_message(source, citation)
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
    def _format_message(source: Work, citation: Citation) -> str:
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
        if citation.citing_url:
            safe_url = html.escape(citation.citing_url, quote=True)
            lines.append(f'<a href="{safe_url}">Çalışmayı aç</a>')
        return "\n".join(lines)
