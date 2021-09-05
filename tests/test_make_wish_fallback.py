import logging
import os
import unittest

from dotenv import load_dotenv

from src.constants import toplevel_buttons, MAKE_WISH, cancel_wish_making
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

    if not os.path.exists("tests/test_data/.testenv"):
        raise RuntimeError(".testenv not found")

    load_dotenv("tests/test_data/.testenv")


class TestMakeWishFallback(unittest.TestCase):
    tg_client_wrapper_0 = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.tg_client_wrapper_0 = ClientHelper("tests/test_data/sess")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tg_client_wrapper_0.close()

    def setUp(self) -> None:
        test_conf = TestConf(
            db_url="",
            bot_token=os.environ["BOT_TOKEN"],
            admin_ids=[99988303],
            arthur_id=99988303,
        )
        self.conversation_helper = ConversationHelper(
            test_conf, self.tg_client_wrapper_0.client
        )

    def tearDown(self) -> None:
        self.conversation_helper.stop_bot()

    def test_cancelation(self):
        control_msg_0 = self.conversation_helper.login_bot()
        control_msg_0.click(text=toplevel_buttons[MAKE_WISH])
        wish_msg = self.conversation_helper.get_unread_messages()
        wish_msg.click(text=cancel_wish_making)
        returned_to_main_menu = self.conversation_helper.get_unread_messages()
        check_intro_markup(self, returned_to_main_menu)
