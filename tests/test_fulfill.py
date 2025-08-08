# Tests requiring actual Telegram session have been commented out.
"""
import logging
import os
import time
import unittest

from dotenv import load_dotenv

import src.constants
from tests.utils import ClientHelper, TestConf, ConversationHelper


# noinspection PyPep8Naming
def setUpModule():
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s: "
        "%(levelname)s: "
        "%(funcName)s(): "
        "%(lineno)d:\t"
        "%(message)s",
    )

    load_dotenv("tests/test_data/.testenv")


class TestFulfill(unittest.TestCase):
    tg_client_wrapper_0 = None
    tg_client_wrapper_1 = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.tg_client_wrapper_0 = ClientHelper("tests/test_data/sess")
        cls.tg_client_wrapper_1 = ClientHelper("tests/test_data/sess2")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tg_client_wrapper_0.close()
        cls.tg_client_wrapper_1.close()

    def setUp(self) -> None:
        test_conf = TestConf(
            db_url="",
            bot_token=os.environ["BOT_TOKEN"],
            admin_ids=[99988303],
            arthur_id=99988303,
        )
        self.conversation_helper = ConversationHelper(
            test_conf, self.tg_client_wrapper_0.client, self.tg_client_wrapper_1.client
        )

    def tearDown(self) -> None:
        self.conversation_helper.stop_bot()

    def test_fulfill(self):
        control_msg_0 = self.conversation_helper.login_bot()
        control_msg_0.click(
            text=src.constants.toplevel_buttons[src.constants.MAKE_WISH]
        )
        wish_txt = "Some wish text"
        self.conversation_helper.send_message(wish_txt)
        time.sleep(1)
        self.conversation_helper.mark_read()

        self.conversation_helper.switch_client()
        control_msg_1 = self.conversation_helper.login_bot()
        control_msg_1.click(
            text=src.constants.toplevel_buttons[src.constants.SELECT_WISH]
        )
        wish_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(wish_msg.text, wish_txt)
        wish_msg.click(text="Взять")
        wish_reply_msg = self.conversation_helper.get_unread_messages()
        phone = self.tg_client_wrapper_0.me.phone
        if not phone.startswith("+"):
            phone = "+" + phone
        wish_reply_txt = src.constants.wish_taken.format(
            wish_text=wish_txt,
            creator_name=self.tg_client_wrapper_0.me.first_name,
            creator_phone=phone,
        )
        self.assertEqual(wish_reply_msg.text, wish_reply_txt)

        self.conversation_helper.switch_client()
        msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(msg.text, src.constants.magick_begins)

    def test_wish_limit(self):
        control_msg_0 = self.conversation_helper.login_bot()
        for i in range(4):
            control_msg_0.click(
                text=src.constants.toplevel_buttons[src.constants.MAKE_WISH]
            )
            wish_txt = "Some wish text" + str(i)
            self.conversation_helper.send_message(wish_txt)
            time.sleep(1)
        self.conversation_helper.mark_read()

        self.conversation_helper.switch_client()
        control_msg_1 = self.conversation_helper.login_bot()
        for _ in range(3):
            control_msg_1.click(
                text=src.constants.toplevel_buttons[src.constants.SELECT_WISH]
            )
            time.sleep(2)
            wish_msg = self.conversation_helper.get_unread_messages()[0]
            wish_msg.click(text="Взять")
        control_msg_1.click(
            text=src.constants.toplevel_buttons[src.constants.SELECT_WISH]
        )
        wish_exceeded_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(wish_exceeded_msg.text, src.constants.wish_limit_str)
"""
