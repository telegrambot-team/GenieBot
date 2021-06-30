import itertools
import logging
import os
import time
import unittest

from dotenv import load_dotenv

from src.button_handlers import is_last_wish
from src.constants import toplevel_buttons, MAKE_WISH, SELECT_WISH, WISHES_TO_SHOW_LIMIT
from tests.utils import ClientHelper, TestConf, ConversationHelper


def group_by(iterable, total_count):
    group_num = 0
    local_count = 0

    def key_fn(_):
        nonlocal group_num
        nonlocal local_count
        if local_count == total_count:
            group_num += 1
            local_count = 0
        local_count += 1
        return group_num

    for k, g in itertools.groupby(iterable, key=key_fn):
        yield g


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

    def testMultipleWishesListing(self):
        control_msg_0 = self.conversation_helper.login_bot()
        wish_txt = "Some wish text"
        wish_list = []
        for i in range(11):
            new_wish = wish_txt + str(i)
            wish_list.append(new_wish)
            control_msg_0.click(text=toplevel_buttons[MAKE_WISH])
            self.conversation_helper.send_message(new_wish)
            time.sleep(1)
        self.conversation_helper.mark_read()

        self.conversation_helper.switch_client()
        control_msg_1 = self.conversation_helper.login_bot()
        control_msg_1.click(text=toplevel_buttons[SELECT_WISH])
        time.sleep(5)
        wishes_msg_1_page = self.conversation_helper.get_unread_messages()
        wish_groups = [
            list(reversed(list(grp)))
            for grp in group_by(reversed(wish_list), WISHES_TO_SHOW_LIMIT)
        ]
        self.assertListEqual(
            wish_groups[0], list(map(lambda x: x.text, wishes_msg_1_page))
        )
        wishes_msg_1_page[0].click(i=1, j=2)
        time.sleep(5)
        wishes_msg_2_page = self.conversation_helper.get_unread_messages()
        self.assertListEqual(
            wish_groups[1], list(map(lambda x: x.text, wishes_msg_2_page))
        )
        wishes_msg_2_page[0].click(i=1, j=2)
        time.sleep(5)
        wishes_msg_3_page = self.conversation_helper.get_unread_messages()
        self.assertListEqual(
            wish_groups[2], list(map(lambda x: x.text, [wishes_msg_3_page]))
        )
        wishes_msg_3_page.click(i=1, j=0)
        time.sleep(5)
        wishes_msg_2_page_new = self.conversation_helper.get_unread_messages()
        self.assertListEqual(
            wish_groups[1], list(map(lambda x: x.text, wishes_msg_2_page_new))
        )

    def test_is_last_wish(self):
        self.assertTrue(is_last_wish(0, 5, 6, WISHES_TO_SHOW_LIMIT))
        self.assertFalse(is_last_wish(2, 5, 10, WISHES_TO_SHOW_LIMIT))
        self.assertTrue(is_last_wish(0, 0, 1, WISHES_TO_SHOW_LIMIT))
        self.assertTrue(is_last_wish(4, 0, 6, WISHES_TO_SHOW_LIMIT))
