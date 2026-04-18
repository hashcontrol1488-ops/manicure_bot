import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    admin_id: int
    channel_id: int | None
    channel_link: str | None
    db_path: str


def load_config() -> Config:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_raw = os.getenv("ADMIN_ID", "0").strip()
    channel_id_raw = os.getenv("CHANNEL_ID", "").strip()
    channel_link = os.getenv("CHANNEL_LINK", "").strip() or None
    db_path = os.getenv("DB_PATH", "database/bot.db").strip()

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")
    if not admin_id_raw.isdigit():
        raise ValueError("ADMIN_ID must be integer")
    channel_id: int | None = None
    if channel_id_raw:
        if channel_id_raw.startswith("-"):
            if not channel_id_raw[1:].isdigit():
                raise ValueError("CHANNEL_ID must be integer")
        elif not channel_id_raw.isdigit():
            raise ValueError("CHANNEL_ID must be integer")
        channel_id = int(channel_id_raw)

    return Config(
        bot_token=bot_token,
        admin_id=int(admin_id_raw),
        channel_id=channel_id,
        channel_link=channel_link,
        db_path=db_path,
    )
