import pytest

from citation_radar.models import Citation, Work
from citation_radar.notifier import NotificationError, TelegramNotifier
from citation_radar.openalex import OpenAlexError


def test_totals_include_zero_and_omit_unavailable():
    source = Work("W1", "Source", None, 2024, None)
    citation = Citation("W1", "W2", "Citing", 2026, None, None)
    text = TelegramNotifier._format_message(source, citation, work_total=0, author_total=18)
    assert "Makalenin toplam atfı (OpenAlex):</b> 0" in text
    assert "Araştırmacının toplam atfı (OpenAlex):</b> 18" in text
    assert "toplam atfı" not in TelegramNotifier._format_message(source, citation)


def test_totals_cached_and_failure_does_not_prevent_delivery(monkeypatch):
    calls = []
    messages = []

    class Client:
        def citation_total(self, entity, entity_id):
            calls.append((entity, entity_id))
            if entity == "authors":
                raise OpenAlexError("Unavailable")
            return 5

    class Response:
        status_code = 200

        def json(self):
            return {"ok": True}

    def post(*args, **kwargs):
        messages.append(kwargs["json"]["text"])
        return Response()

    monkeypatch.setattr("citation_radar.notifier.httpx.post", post)
    notifier = TelegramNotifier("token", "chat", totals_client=Client(), author_id="A1")
    source = Work("W1", "Source", None, 2024, None)
    citation = Citation("W1", "W2", "Citing", 2026, None, None)
    notifier.send_new_citation(source, citation)
    notifier.send_new_citation(source, citation)
    assert calls == [("works", "W1"), ("authors", "A1")]
    assert len(messages) == 2
    assert "OpenAlex):</b> 5" in messages[0]
    assert "Araştırmacının toplam" not in messages[0]


def test_message_contains_titles():
    source = Work("W1", "Source & Paper", None, 2024, None)
    citation = Citation("W1", "W2", "Citing <Paper>", 2026, "https://doi.org/10.1/x", "https://example.org")
    text = TelegramNotifier._format_message(source, citation)
    assert "Source &amp; Paper" in text
    assert "Citing &lt;Paper&gt;" in text
    assert "2026" in text


def test_message_can_include_compare_links():
    source = Work("W1", "Source", None, 2024, None)
    citation = Citation("W1", "W2", "Citing", 2026, None, None)

    text = TelegramNotifier._format_message(
        source,
        citation,
        compare_sources=("google-scholar", "researchgate"),
        google_scholar_profile_url="https://scholar.google.com/citations?user=test",
        researchgate_profile_url="https://www.researchgate.net/profile/Test-User",
    )

    assert "Çapraz kontrol" in text
    assert "Google Scholar profili" in text
    assert "ResearchGate profili" in text


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
