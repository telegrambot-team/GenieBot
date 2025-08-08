import dataclasses

from dataclasses import dataclass
from functools import lru_cache

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    bot_token: str
    db_url: PostgresDsn | None = None
    admin_ids: list[int]
    arthur_id: int

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("db_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: str | None) -> str | None:
        if not v:
            return None
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://")
        return v

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v: str | list[int]) -> list[int]:
        if isinstance(v, str):
            return [int(part) for part in v.split(";") if part]
        return v


@dataclass
class BotData:
    wishes: dict[str, dict] = dataclasses.field(default_factory=dict)
    config: Config | None = None


@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()
