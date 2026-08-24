import pytest

from citation_radar.models import Citation, Work
from citation_radar.notifier import NotificationError, TelegramNotifier


def test_message_contains_titles():
    source = Work("W1", "Source & Paper", None, 2024, None)
    citation = Citation("W1", "W2", "Citing <Paper>", 2026, "https://doi.org/10.1/x", "https://example.org")
    text = TelegramNotifier._format_message(source, citation)
    assert "Source &amp; Paper" in text
    assert "Citing &lt;Paper&gt;" in text
    assert "2026" in text


def test_send_new_citation_raises_on_telegram_api_error(monkeypatch):
    class DummyResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"ok": False, "description": "chat not found"}

    def fake_post(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("citation_radar.notifier.httpx.post", fake_post)

    notifier = TelegramNotifier("token", "chat")
    source = Work("W1", "Source", None, 2024, None)
    citation = Citation("W1", "W2", "Citing", 2026, None, None)

    with pytest.raises(NotificationError, match="chat not found"):
        notifier.send_new_citation(source, citation)
