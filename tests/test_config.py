from pathlib import Path

from citation_radar.config import load_settings


def test_database_path_is_resolved_relative_to_dotenv(monkeypatch, tmp_path: Path):
    root = tmp_path / "project"
    nested = root / "nested"
    root.mkdir()
    nested.mkdir()
    (root / ".env").write_text("DATABASE_PATH=./state/citation_radar.db\n", encoding="utf-8")

    state_dir = root / "state"
    state_dir.mkdir()

    monkeypatch.chdir(nested)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.delenv("OPENALEX_EMAIL", raising=False)
    monkeypatch.delenv("OPENALEX_AUTHOR_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    settings = load_settings()

    assert settings.database_path == root / "state" / "citation_radar.db"
