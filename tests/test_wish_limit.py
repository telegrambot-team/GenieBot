import sys
import types
import unittest
from types import SimpleNamespace

# Create minimal stubs for telegram modules so tests can run without the
# actual telegram package installed.
telegram = types.ModuleType("telegram")
telegram.Update = object


class _Dummy:
    def __init__(self, *args, **kwargs):
        pass


telegram.InlineKeyboardMarkup = _Dummy
telegram.InlineKeyboardButton = _Dummy
telegram.ReplyKeyboardMarkup = _Dummy
telegram.KeyboardButton = _Dummy
telegram.error = types.ModuleType("telegram.error")
telegram.error.BadRequest = Exception
telegram.bot = types.ModuleType("telegram.bot")
telegram.bot.log = lambda f: f
telegram.ext = types.ModuleType("telegram.ext")


class _ConversationHandler:
    END = object()


telegram.ext.ConversationHandler = _ConversationHandler
telegram.ext.CallbackContext = object
sys.modules.setdefault("telegram", telegram)
sys.modules.setdefault("telegram.error", telegram.error)
sys.modules.setdefault("telegram.bot", telegram.bot)
sys.modules.setdefault("telegram.ext", telegram.ext)

from telegram.ext import ConversationHandler

from src import button_handlers
from src import constants


class DummyMessage:
    def __init__(self, text):
        self.text = text
        self.reply_text_calls = []

    def reply_text(self, text, reply_markup=None):
        self.reply_text_calls.append(text)


class TestWishLimit(unittest.TestCase):
    def _make_ctx(self, created_ids, statuses):
        user_data = {"contact": ("name", "phone"), "wishes": {"created": created_ids, "in_progress": [], "done": []}}
        wishes = {str(wid): {"status": status, "creator_id": 1} for wid, status in zip(created_ids, statuses)}
        bot_data = SimpleNamespace(wishes=wishes)
        ctx = SimpleNamespace(user_data=user_data, bot_data=bot_data)
        return ctx

    def _make_update(self):
        msg = DummyMessage(constants.toplevel_buttons[constants.MAKE_WISH])
        update = SimpleNamespace(message=msg, effective_user=SimpleNamespace(id=1))
        return update, msg

    def test_fulfilled_wishes_not_counted(self):
        created_ids = list(range(8))
        statuses = [constants.DONE] * 5 + [constants.WAITING] * 3
        ctx = self._make_ctx(created_ids, statuses)
        update, msg = self._make_update()

        result = button_handlers.button_handler(update, ctx)

        self.assertEqual(result, constants.MAKE_WISH)
        self.assertEqual(msg.reply_text_calls[0], constants.waiting_for_wish)

    def test_limit_enforced_for_active_wishes(self):
        created_ids = list(range(7))
        statuses = [constants.WAITING] * 7
        ctx = self._make_ctx(created_ids, statuses)
        update, msg = self._make_update()

        result = button_handlers.button_handler(update, ctx)

        self.assertEqual(result, ConversationHandler.END)
        self.assertTrue(msg.reply_text_calls[0].startswith("\N{GENIE}Ты уже загадал максимум желаний!"))


if __name__ == "__main__":
    unittest.main()
