import logging
import os
import time
import unittest

from dotenv import load_dotenv

from src.constants import (
    start_msg,
    request_contact_text,
    intro_msg,
    waiting_for_wish,
    lock_and_load,
    no_self_created_wishes,
    toplevel_buttons,
    MY_WISHES,
    MAKE_WISH, delete_wish_btn_txt,
)
from tests.utils import ClientHelper, TestConf, ConversationHelper, check_intro_markup


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


def check_start_msg(self, msg):
    self.assertEqual(msg.text, start_msg)
    self.assertEqual(msg.reply_markup.rows[0].buttons[0].text, request_contact_text)


def check_intro_msg(self, msg):
    self.assertEqual(msg.text, intro_msg)


class TestCrudWishes(unittest.TestCase):
    tg_client_wrapper = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.tg_client_wrapper = ClientHelper("tests/test_data/sess")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tg_client_wrapper.close()

    def setUp(self) -> None:
        test_conf = TestConf(
            db_url="",
            bot_token=os.environ["BOT_TOKEN"],
            admin_ids=[99988303],
            arthur_id=99988303,
        )
        self.conversation_helper = ConversationHelper(
            test_conf, self.tg_client_wrapper.client
        )

    def tearDown(self) -> None:
        self.conversation_helper.stop_bot()

    def test_start(self):
        self.conversation_helper.send_message("/start")
        msg = self.conversation_helper.get_unread_messages()
        check_start_msg(self, msg)

        self.conversation_helper.send_message("23525")
        msg = self.conversation_helper.get_unread_messages()
        check_start_msg(self, msg)

        msg = self.conversation_helper.login_bot()
        check_intro_msg(self, msg)
        check_intro_markup(self, msg)

    def test_crud(self):
        control_msg = self.conversation_helper.login_bot()
        control_msg.click(text=toplevel_buttons[MY_WISHES])
        new_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_msg.text, no_self_created_wishes)

        # добавляем первое
        control_msg.click(text=toplevel_buttons[MAKE_WISH])
        new_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_msg.text, waiting_for_wish)
        wish_txt_0 = "wgregueng 230t23j\nefowefn110"
        wish_txt_1 = "vvvwewegergre 230t23j\needewdew"
        self.conversation_helper.send_message(wish_txt_0)
        new_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_msg.text, lock_and_load)

        # проверяем, что добавилось
        control_msg.click(text=toplevel_buttons[MY_WISHES])
        new_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_msg.text, wish_txt_0)
        self.assertEqual(len(new_msg.buttons), 1)
        self.assertEqual(len(new_msg.buttons[0]), 1)
        self.assertEqual(new_msg.buttons[0][0].text, delete_wish_btn_txt)

        # добавляем второе
        control_msg.click(text=toplevel_buttons[MAKE_WISH])
        self.conversation_helper.mark_read()
        self.conversation_helper.send_message(wish_txt_1)
        time.sleep(1)
        new_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_msg.text, lock_and_load)

        # проверяем, что добавилось
        control_msg.click(text=toplevel_buttons[MY_WISHES])
        time.sleep(1)
        new_messages = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_messages[1].text, wish_txt_0)
        self.assertEqual(new_messages[0].text, wish_txt_1)
        new_messages[0].click(text="Удалить")

        # удаляем второе
        control_msg.click(text=toplevel_buttons[MY_WISHES])
        new_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_msg.text, wish_txt_0)

        # удаляем первое
        new_msg.click(text="Удалить")
        control_msg.click(text=toplevel_buttons[MY_WISHES])
        new_msg = self.conversation_helper.get_unread_messages()
        self.assertEqual(new_msg.text, no_self_created_wishes)
