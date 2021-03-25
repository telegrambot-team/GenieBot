import contextlib
import itertools
import logging
import os
import time
import traceback
from dataclasses import dataclass

from telethon.sync import TelegramClient
from telethon.tl import functions

from src.constants import MAKE_WISH, toplevel_buttons, SELECT_WISH, FULFILLED_LIST, MY_WISHES, WISHES_IN_PROGRESS
from src.main import create_bot


class ClientHelper:
    def __init__(self, session_path):
        self.stack = contextlib.ExitStack()
        api_id = int(os.environ['API_ID'])
        api_hash = os.environ['API_HASH']
        self.client = TelegramClient(session_path, api_id, api_hash)
        self.resource = self.stack.enter_context(self.client)
        self.me = self.client.get_me()

    def close(self):
        self.stack.close()


@dataclass
class TestConf:
    db_url: str
    bot_token: str
    tg_client_0: TelegramClient
    tg_client_1: TelegramClient = None


class ConversationHelper:
    def __init__(self, conf: TestConf):
        self.tg_client_0 = conf.tg_client_0
        self.tg_client_1 = conf.tg_client_1
        self.bot_updater = create_bot(conf)
        self.bot_name = self.bot_updater.bot.name
        self.bot_updater.start_polling()
        self.mark_read(self.tg_client_0)
        if self.tg_client_1:
            self.mark_read(self.tg_client_1)
        self.current_client = self.tg_client_0
        time.sleep(0.5)

    def stop_bot(self):
        self.bot_updater.stop()

    def get_unread_count(self):
        # noinspection PyTypeChecker
        result = self.current_client(functions.messages.GetPeerDialogsRequest(
            peers=[self.bot_name]
        ))
        return result.dialogs[0].unread_count

    def send_message(self, txt):
        # noinspection PyTypeChecker
        msg = self.current_client.send_message(self.bot_name, txt)
        return msg

    def mark_read(self, client=None):
        if client is None:
            client = self.current_client
        # noinspection PyTypeChecker
        client.send_read_acknowledge(self.bot_name)

    def get_unread_messages(self, timeout=10):
        now = time.time()
        while True:
            # noinspection PyTypeChecker
            unread_count = self.get_unread_count()
            if unread_count:
                # noinspection PyTypeChecker
                lst = [m for m in itertools.islice(self.current_client.iter_messages(self.bot_name),
                                                   unread_count) if m.sender.bot]
                # noinspection PyTypeChecker
                self.current_client.send_read_acknowledge(self.bot_name)
                logging.info([m.text for m in lst])
                return lst[0] if len(lst) == 1 else lst
            if now + timeout < time.time():
                break
            time.sleep(0.1)
        raise TimeoutError("No messages delivered in time")

    def login_bot(self):
        self.send_message('/start')
        msg = self.get_unread_messages()
        msg.click(share_phone=True)
        return self.get_unread_messages()

    def switch_client(self):
        if self.current_client is self.tg_client_0:
            self.current_client = self.tg_client_1
        else:
            self.current_client = self.tg_client_0


@contextlib.contextmanager
def scoped_bot(conf):
    bot = ConversationHelper(conf)
    try:
        yield bot
    except:
        traceback.print_exc()
        raise
    finally:
        bot.stop_bot()


def check_intro_markup(self, msg):
    self.assertEqual(msg.reply_markup.rows[0].buttons[0].text,
                     toplevel_buttons[MAKE_WISH])
    self.assertEqual(msg.reply_markup.rows[0].buttons[1].text,
                     toplevel_buttons[SELECT_WISH])
    self.assertEqual(msg.reply_markup.rows[1].buttons[0].text,
                     toplevel_buttons[FULFILLED_LIST])
    self.assertEqual(msg.reply_markup.rows[1].buttons[1].text,
                     toplevel_buttons[MY_WISHES])
    self.assertEqual(msg.reply_markup.rows[1].buttons[2].text,
                     toplevel_buttons[WISHES_IN_PROGRESS])
