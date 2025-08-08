import logging
import traceback

from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict

from sqlalchemy import JSON, Column, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from telegram.ext import BasePersistence

from src import config

logger = logging.getLogger(__name__)

Base = declarative_base()


@contextmanager
def session_scope(session_cls):
    """Provide a transactional scope around a series of operations."""
    session = session_cls()
    try:
        yield session
        session.commit()
    except Exception:
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()


class Document:
    id = Column(Integer, primary_key=True)
    data = Column(JSON)


class UserData(Base, Document):
    __tablename__ = "user_persdata"


class ChatData(Base, Document):
    __tablename__ = "chat_persdata"


class BotData(Base, Document):
    __tablename__ = "bot_persdata"


class ConversationData(Base, Document):
    __tablename__ = "conversation"


class DBPersistence(BasePersistence):
    def __init__(self, connection_string: str):
        super().__init__()
        self.connection_string = connection_string
        self.user_data = defaultdict(dict)
        self.chat_data = defaultdict(dict)
        self.bot_data = config.BotData()
        self.conversation_data = {}
        connect_args = {}
        if self.connection_string.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        self.engine = create_engine(self.connection_string, connect_args=connect_args)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.load_data()

    def load_data(self):
        with session_scope(self.Session) as session:
            self._load(session, from_table=UserData, dst=self.user_data)
            self._load(session, from_table=ChatData, dst=self.chat_data)
            bot_data_from_table: dict[int, dict] = {}
            self._load(session, from_table=BotData, dst=bot_data_from_table)
            if 0 in bot_data_from_table:
                self.bot_data = config.BotData(**bot_data_from_table[0])
            self._load(session, from_table=ConversationData, dst=self.conversation_data)

    @staticmethod
    def _load(session, from_table, dst):
        logger.info("Loading state %s", from_table.__tablename__)
        result = session.query(from_table).all()
        for row in result:
            dst[row.id] = row.data

    def get_conversations(self, name):
        conversations_by_name = {}
        for user_id, conv_dict in self.conversation_data.items():
            conversations_by_name[user_id,] = conv_dict.get(name, None)
        return conversations_by_name

    def update_conversation(self, name, key, new_state):
        (chat_id,) = key
        if self.conversation_data.setdefault(chat_id, {}).get(name) == new_state:
            return
        logger.info("Updating conversation %s with %s=%s", name, key, new_state)
        self.conversation_data[chat_id][name] = new_state
        with session_scope(self.Session) as session:
            session.merge(
                ConversationData(
                    id=chat_id,
                    data=self.conversation_data[chat_id],
                )
            )

    def get_user_data(self):
        return deepcopy(self.user_data)

    def update_user_data(self, user_id, data):
        logger.info("Updating %s with %s", user_id, data)
        self.user_data[user_id] = data
        with session_scope(self.Session) as session:
            session.merge(UserData(id=user_id, data=data))

    def flush(self):
        with session_scope(self.Session) as session:
            for user_id, data in self.user_data.items():
                session.merge(UserData(id=user_id, data=data))
            for chat_id, data in self.chat_data.items():
                session.merge(ChatData(id=chat_id, data=data))
            session.merge(BotData(id=0, data=asdict(self.bot_data)))
            for chat_id, data in self.conversation_data.items():
                session.merge(ConversationData(id=chat_id, data=data))
        self.engine.dispose()

    def get_chat_data(self):
        return deepcopy(self.chat_data)

    def get_bot_data(self):
        return deepcopy(self.bot_data)

    def update_chat_data(self, chat_id, data):
        logger.info("Updating %s with %s", chat_id, data)
        self.chat_data[chat_id] = data
        with session_scope(self.Session) as session:
            session.merge(ChatData(id=chat_id, data=data))

    def update_bot_data(self, data):
        logger.info("Updating bot_data with %s", data)
        self.bot_data = data
        with session_scope(self.Session) as session:
            session.merge(BotData(id=0, data=asdict(data)))


if __name__ == "__main__":
    pers = DBPersistence("postgresql://")
    ch = pers.user_data[267932259]
    del ch["wishes"]["in_progress"][2]
    pers.update_user_data(267932259, ch)
