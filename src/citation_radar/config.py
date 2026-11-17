from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    openalex_api_key: str | None
    openalex_email: str | None
    openalex_author_id: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    database_path: Path
    notification_compare_sources: tuple[str, ...]
    google_scholar_profile_url: str | None
    researchgate_profile_url: str | None


def _parse_compare_sources(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()

    aliases = {
        "google-scholar": "google-scholar",
        "google_scholar": "google-scholar",
        "scholar": "google-scholar",
        "researchgate": "researchgate",
        "research_gate": "researchgate",
    }
    parsed: list[str] = []
    unknown: list[str] = []
    for raw_item in value.split(","):
        item = raw_item.strip().lower()
        if not item:
            continue
        normalized = aliases.get(item)
        if normalized is None:
            unknown.append(raw_item.strip())
            continue
        if normalized not in parsed:
            parsed.append(normalized)

    if unknown:
        supported = ", ".join(sorted(set(aliases.values())))
        unknown_values = ", ".join(unknown)
        raise ConfigError(
            f"Unsupported NOTIFICATION_COMPARE_SOURCES value(s): {unknown_values}. "
            f"Supported values: {supported}."
        )

    return tuple(parsed)


def load_settings() -> Settings:
    dotenv_path = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path or None)
    database_path = Path(os.getenv("DATABASE_PATH", "./citation_radar.db")).expanduser()
    if dotenv_path and not database_path.is_absolute():
        database_path = Path(dotenv_path).resolve().parent / database_path

    return Settings(
        openalex_api_key=os.getenv("OPENALEX_API_KEY"),
        openalex_email=os.getenv("OPENALEX_EMAIL"),
        openalex_author_id=os.getenv("OPENALEX_AUTHOR_ID"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        database_path=database_path,
        notification_compare_sources=_parse_compare_sources(os.getenv("NOTIFICATION_COMPARE_SOURCES")),
        google_scholar_profile_url=os.getenv("GOOGLE_SCHOLAR_PROFILE_URL"),
        researchgate_profile_url=os.getenv("RESEARCHGATE_PROFILE_URL"),
    )
