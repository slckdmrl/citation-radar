from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


@dataclass(frozen=True)
class Settings:
    openalex_api_key: str | None
    openalex_email: str | None
    openalex_author_id: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    database_path: Path


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
    )
