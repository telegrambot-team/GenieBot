import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from typing import List

config_instance = None


@dataclass(frozen=True)
class PingerConfig:
    api_id: int
    api_hash: str
    bot_list: List[str]
    msg_timeout: int
    pinger_sleep_time: int


@dataclass(frozen=True)
class Config:
    bot_token: str
    db_url: str
    admin_ids: List[int]
    arthur_id: int
    pinger_enabled: bool
    pinger_config: PingerConfig


@dataclass
class BotData:
    wishes: dict[int, dict]
    config: Config


def get_config():
    # TODO: Should be passed to bot only once to prevent getting variables from separate configs
    global config_instance
    if config_instance:
        return config_instance

    load_dotenv()
    token = os.environ['BOT_TOKEN']
    database_url = os.environ.get('DATABASE_URL') or ''
    admin_ids = list(map(int, os.environ['ADMIN_IDS'].split(';')))
    arthur_id = int(os.environ['ARTHUR_ID'])
    pinger_enabled = True

    try:
        api_id = int(os.environ['PINGER_API_ID'])
        api_hash = os.environ['PINGER_API_HASH']
        bot_list = os.environ['PINGER_BOT_LIST'].split(';')
        msg_timeout = int(os.environ.get('MSG_TIMEOUT', 15))
        pinger_sleep_time = int(os.environ.get('PINGER_SLEEP_TIME', 10))
        pinger_config = PingerConfig(
            api_id=api_id,
            api_hash=api_hash,
            bot_list=bot_list,
            msg_timeout=msg_timeout,
            pinger_sleep_time=pinger_sleep_time
        )
    except KeyError as e:
        logging.info(repr(e))
        logging.info('Disabling pinger')
        pinger_enabled = False
        pinger_config = None

    config_instance = Config(
        bot_token=token,
        db_url=database_url,
        admin_ids=admin_ids,
        arthur_id=arthur_id,
        pinger_enabled=pinger_enabled,
        pinger_config=pinger_config
    )
    return config_instance
