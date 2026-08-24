from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openalex_email: str | None
    openalex_author_id: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    database_path: Path


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        openalex_email=os.getenv("OPENALEX_EMAIL"),
        openalex_author_id=os.getenv("OPENALEX_AUTHOR_ID"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        database_path=Path(os.getenv("DATABASE_PATH", "./citation_radar.db")),
    )
