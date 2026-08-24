from citation_radar.models import Citation, Work
from citation_radar.notifier import TelegramNotifier


def test_message_contains_titles():
    source = Work("W1", "Source & Paper", None, 2024, None)
    citation = Citation("W1", "W2", "Citing <Paper>", 2026, "https://doi.org/10.1/x", "https://example.org")
    text = TelegramNotifier._format_message(source, citation)
    assert "Source &amp; Paper" in text
    assert "Citing &lt;Paper&gt;" in text
    assert "2026" in text
