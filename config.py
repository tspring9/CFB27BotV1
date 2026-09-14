import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    token: str
    guild_ids: list[int]
    sheet_url: str


def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")

    sheet_url = os.getenv("SHEET_URL", "").strip()
    if not sheet_url:
        raise SystemExit("SHEET_URL is not set. Use the sheet's File > Share > Publish to web link.")

    # One or more server IDs, comma-separated
    guild_ids = [int(part) for part in os.getenv("GUILD_ID", "").replace(" ", "").split(",") if part]
    return Settings(token=token, guild_ids=guild_ids, sheet_url=sheet_url)
