import json
import logging
from builtins import property
from collections import defaultdict
from copy import deepcopy

import psycopg2
from psycopg2.extras import Json, DictCursor
from telegram.ext import BasePersistence


class PSQLDatabase:
    def __init__(self, connection_string):
        self._conn = psycopg2.connect(connection_string)
        self._conn.autocommit = True
        self._cursor = self._conn.cursor(cursor_factory=DictCursor)

    def query(self, query, *params):
        result = self._cursor.execute(query, *params)
        logging.info(self._cursor.statusmessage)
        return result

    def close(self):
        return self._conn.close()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def closed(self):
        return self._conn.closed


class PostgresPersistence(BasePersistence):
    USER_TABLE = 'user_data'
    CONVERSATION_TABLE = 'conversation_data'

    def __init__(self, connection_string):
        super().__init__(store_bot_data=False,
                         store_chat_data=False)
        self.connection_string = connection_string
        self.user_data = defaultdict(dict)
        self.conversation_data = {}
        self._db = PSQLDatabase(connection_string)
        self.create_db()
        self.load_data()

    def create_db(self):
        self._db.query(f'create table IF NOT EXISTS {self.USER_TABLE} (id integer PRIMARY KEY, data JSONB);')
        self._db.query(f'create table IF NOT EXISTS {self.CONVERSATION_TABLE} (id integer PRIMARY KEY, data JSONB);')

    def load_data(self):
        self._load(from_table=self.USER_TABLE, dst=self.user_data)
        self._load(from_table=self.CONVERSATION_TABLE, dst=self.conversation_data)

    def _load(self, from_table, dst):
        logging.info(f"Loading state {from_table=}")
        self._db.query(f'select id, data from {from_table}')
        result = self._db.fetchall()
        for row in result:
            dst[row['id']] = row['data']

    def get_conversations(self, name):
        conversations_by_name = {}
        for user_id, conv_dict in self.conversation_data.items():
            conversations_by_name[user_id, ] = conv_dict.get(name, None)
        return conversations_by_name

    def update_conversation(self, name, key, new_state):
        chat_id, = key
        if self.conversation_data.setdefault(chat_id, {}).get(name) == new_state:
            return
        logging.info(f"Updating conversation {name}"
                     f" with {key=}={new_state}")
        self.conversation_data[chat_id][name] = new_state
        self._upsert(chat_id, self.conversation_data[chat_id], self.CONVERSATION_TABLE)

    def _upsert(self, key, data, table):
        ins_data = Json(data, json.dumps)
        self._db.query(
            f'insert into {table} (id, data) values ({key}, {ins_data})'
            'ON CONFLICT (id)'
            'DO UPDATE SET (id, data) = (EXCLUDED.id, EXCLUDED.data)'
        )

    def get_user_data(self):
        return deepcopy(self.user_data)

    def update_user_data(self, user_id, data):
        if self.user_data.get(user_id) == data:
            return
        logging.info(f"Updating {user_id} with {data}")
        self.user_data[user_id] = data
        self._upsert(user_id, data, self.USER_TABLE)

    def flush(self):
        for user_id, data in self.user_data.items():
            self._upsert(user_id, data, self.USER_TABLE)
        for user_id, data in self.conversation_data.items():
            self._upsert(user_id, data, self.CONVERSATION_TABLE)
        self._db.close()

    def get_chat_data(self):
        raise NotImplementedError("shouldn't be called")

    def get_bot_data(self):
        raise NotImplementedError("shouldn't be called")

    def update_chat_data(self, chat_id, data):
        raise NotImplementedError("shouldn't be called")

    def update_bot_data(self, data):
        raise NotImplementedError("shouldn't be called")
