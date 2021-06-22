import logging
import os
import shutil
import tempfile
import unittest

from dotenv import load_dotenv

from src.constants import default_handler_text
from src.db_persistence import DBPersistence
from tests.utils import TestConf, ClientHelper, scoped_bot, check_intro_markup


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


class TestPersistence(unittest.TestCase):
    tg_client_wrapper = None
    db_file = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.tg_client_wrapper = ClientHelper("tests/test_data/sess")
        cls.db_file = os.path.join(tempfile.mkdtemp(), "sqlite.db")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(os.path.dirname(cls.db_file))
        cls.tg_client_wrapper.close()

    def setUp(self) -> None:
        self.test_conf = TestConf(
            db_url="sqlite:///" + self.db_file,
            bot_token=os.environ["BOT_TOKEN"],
            admin_ids=[99988303],
            arthur_id=99988303,
        )

    def test_contact_persists(self):
        with scoped_bot(self.test_conf, self.tg_client_wrapper.client) as helper:
            helper.login_bot()

        with scoped_bot(self.test_conf, self.tg_client_wrapper.client) as helper:
            helper.send_message("123")
            msg = helper.get_unread_messages()
            self.assertEqual(msg.text, default_handler_text)
            check_intro_markup(self, msg)

        loader = DBPersistence(self.test_conf.db_url)
        self.assertEqual(len(loader.user_data), 1)
        self.assertIn(self.tg_client_wrapper.me.id, loader.user_data)
        phone = self.tg_client_wrapper.me.phone
        if not phone.startswith("+"):
            phone = "+" + phone
        self.assertDictEqual(
            loader.user_data[self.tg_client_wrapper.me.id],
            {
                "contact": [self.tg_client_wrapper.me.first_name, phone],
                "wishes": {"created": [], "in_progress": [], "done": []},
            },
        )
