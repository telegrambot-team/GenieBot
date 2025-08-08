import dataclasses
import os

from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    db_url: str
    admin_ids: list[int]
    arthur_id: int


@dataclass
class BotData:
    wishes: dict[str, dict] = dataclasses.field(default_factory=dict)
    config: Config | None = None


@lru_cache(maxsize=1)
def get_config() -> Config:
    load_dotenv()
    token = os.environ["BOT_TOKEN"]
    database_url = os.environ.get("DATABASE_URL") or ""
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://")
    admin_ids = list(map(int, os.environ["ADMIN_IDS"].split(";")))
    arthur_id = int(os.environ["ARTHUR_ID"])
    return Config(bot_token=token, db_url=database_url, admin_ids=admin_ids, arthur_id=arthur_id)
