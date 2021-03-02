import logging

from telegram import Update
from telegram.bot import log
from telegram.ext import CallbackContext, ConversationHandler

from constants import toplevel_buttons, Buttons


def incorrect_wish_handler(update: Update, _: CallbackContext):
    update.message.reply_text("Я только читать умею, ты текстом пиши")
    return Buttons.MAKE_WISH


def make_wish_handler(update: Update, ctx: CallbackContext):
    if 'wishes' not in ctx.user_data:
        ctx.user_data['wishes'] = []
    ctx.user_data['wishes'].append(update.message.text)
    update.message.reply_text('Слушаюсь и повинуюсь')
    return ConversationHandler.END


def list_my_wishes(update: Update, ctx: CallbackContext):
    text = '\n'.join(ctx.user_data['wishes'])
    update.message.reply_text(text)
    # TODO: undo a wish
    return ConversationHandler.END



@log
def button_handler(update: Update, ctx: CallbackContext):
    text = update.message.text
    if text == toplevel_buttons[Buttons.MAKE_WISH]:
        update.message.reply_text("Отправь мне своё желание")
        return Buttons.MAKE_WISH
    elif text == toplevel_buttons[Buttons.FULFILL_WISH]:
        update.message.reply_text("Pilonia&Kingsman: исполним даже то, чего вы не желали")
        # TODO: create handler
        return ConversationHandler.END
    elif text == toplevel_buttons[Buttons.FULFILLED_LIST]:
        update.message.reply_text("Вы ещё не выполнили ни одного желания")
        # TODO: create handler
        return ConversationHandler.END
    elif text == toplevel_buttons[Buttons.TODO_WISHES]:
        update.message.reply_text("Вы ещё не взяли на себя ни одного желания")
        # TODO: create handler
        return ConversationHandler.END
    elif text == toplevel_buttons[Buttons.MY_WISHES]:
        list_my_wishes(update, ctx)
        return ConversationHandler.END
