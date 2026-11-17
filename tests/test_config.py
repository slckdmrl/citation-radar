from pathlib import Path

import pytest

from citation_radar.config import ConfigError, load_settings


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


def test_compare_sources_are_loaded_from_env(monkeypatch, tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".env").write_text(
        "\n".join(
            [
                "NOTIFICATION_COMPARE_SOURCES=google_scholar,researchgate",
                "GOOGLE_SCHOLAR_PROFILE_URL=https://scholar.google.com/citations?user=test",
                "RESEARCHGATE_PROFILE_URL=https://www.researchgate.net/profile/Test-User",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(root)
    monkeypatch.delenv("NOTIFICATION_COMPARE_SOURCES", raising=False)
    monkeypatch.delenv("GOOGLE_SCHOLAR_PROFILE_URL", raising=False)
    monkeypatch.delenv("RESEARCHGATE_PROFILE_URL", raising=False)

    settings = load_settings()

    assert settings.notification_compare_sources == ("google-scholar", "researchgate")
    assert settings.google_scholar_profile_url == "https://scholar.google.com/citations?user=test"
    assert settings.researchgate_profile_url == "https://www.researchgate.net/profile/Test-User"


def test_invalid_compare_source_raises(monkeypatch, tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".env").write_text("NOTIFICATION_COMPARE_SOURCES=google-scholar,bad-source\n", encoding="utf-8")

    monkeypatch.chdir(root)
    monkeypatch.delenv("NOTIFICATION_COMPARE_SOURCES", raising=False)

    with pytest.raises(ConfigError, match="bad-source"):
        load_settings()
