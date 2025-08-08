import dataclasses
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from typing import List, Optional

config_instance = None


@dataclass
class Config:
    bot_token: str
    db_url: str
    admin_ids: List[int]
    arthur_id: int


@dataclass
class BotData:
    wishes: dict[str, dict] = dataclasses.field(default_factory=dict)
    config: Optional[Config] = None


def get_config():
    global config_instance
    if config_instance:
        return config_instance

    load_dotenv()
    token = os.environ["BOT_TOKEN"]
    database_url = os.environ.get("DATABASE_URL") or ""
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://")
    admin_ids = list(map(int, os.environ["ADMIN_IDS"].split(";")))
    arthur_id = int(os.environ["ARTHUR_ID"])
    config_instance = Config(
        bot_token=token,
        db_url=database_url,
        admin_ids=admin_ids,
        arthur_id=arthur_id,
    )
    return config_instance
