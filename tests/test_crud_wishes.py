import contextlib
import itertools
import os
import time
import unittest
from dataclasses import dataclass

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl import functions

from src.constants import start_msg
from src.main import create_bot


@dataclass
class TestConf:
    db_url: str
    bot_token: str


# noinspection PyTypeChecker
stack: contextlib.ExitStack = None
# noinspection PyTypeChecker
client: TelegramClient = None
resource = None
test_conf = None


def setUpModule():
    load_dotenv('tests/test_data/.testenv')
    global test_conf
    test_conf = TestConf(
        db_url=os.environ['DATABASE_URL'],
        bot_token=os.environ['BOT_TOKEN']
    )
    global stack
    stack = contextlib.ExitStack()
    api_id = int(os.environ['API_ID'])
    api_hash = os.environ['API_HASH']
    global client
    client = TelegramClient('tests/test_data/sess', api_id, api_hash)
    global resource
    resource = stack.enter_context(client)


def tearDownModule():
    stack.close()


class TestCrudWishes(unittest.TestCase):
    def setUp(self) -> None:
        # drop database
        self.bot_updater = create_bot(test_conf)
        self.bot_updater.start_polling()
        self.chat_peer = client.get_input_entity(self.bot_updater.bot.name)
        # noinspection PyTypeChecker
        client.send_read_acknowledge(self.chat_peer)

    def tearDown(self) -> None:
        self.bot_updater.stop()

    def getUnreadCount(self):
        # noinspection PyTypeChecker
        result = client(functions.messages.GetPeerDialogsRequest(
            peers=[self.chat_peer]
        ))
        return result.dialogs[0].unread_count

    def send_message(self, txt):
        msg = client.send_message(
            self.bot_updater.bot.name,
            txt
        )
        return msg

    def getUnreadMessages(self, timeout=10):
        now = time.time()
        while True:
            # noinspection PyTypeChecker
            unread_count = self.getUnreadCount()
            if unread_count:
                # noinspection PyTypeChecker
                lst = list(itertools.islice(client.iter_messages(self.chat_peer),
                                            unread_count))
                return lst[0] if len(lst) == 1 else lst
            if now + timeout < time.time():
                break
            time.sleep(0.1)
        raise TimeoutError("No messages delivered in time")

    def test_start(self):
        self.send_message('/start')
        msg = self.getUnreadMessages()
        self.assertEqual(msg.text, start_msg)

    def test_requesting_contact(self):
        self.send_message('23525')
        msg = self.getUnreadMessages()
        self.assertEqual(msg.text, start_msg)
