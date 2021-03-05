from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.bot import log
from telegram.ext import CallbackContext, ConversationHandler

from config import ARTHUR_ID
from constants import toplevel_buttons, WAITING_FOR_PROOF, MAKE_WISH, \
    SELECT_WISH, FULFILLED_LIST, WISHES_IN_PROGRESS, MY_WISHES, WAITING, REMOVED, IN_PROGRESS, drop_wish_inline_btn, \
    fulfill_wish_inline_btn, take_wish_inline_btn, DONE


def incorrect_wish_handler(update: Update, _: CallbackContext):
    update.message.reply_text("Я только читать умею, ты текстом пиши")
    return MAKE_WISH


def make_wish_handler(update: Update, ctx: CallbackContext):
    if 'wishes' not in ctx.bot_data:
        ctx.bot_data['wishes'] = {}

    wish_id = len(ctx.bot_data['wishes'])
    # new_wish = Wish(wish_id=wish_id,
    #                 creator_id=update.effective_user.id,
    #                 text=update.message.text)
    new_wish = {
        'wish_id': wish_id,
        'creator_id': update.effective_user.id,
        'text': update.message.text,
        'fulfiller_id': None,
        'status': WAITING
    }
    ctx.bot_data['wishes'][wish_id] = new_wish
    ctx.user_data['wishes']['created'].append(wish_id)

    update.message.reply_text('Слушаюсь и повинуюсь')
    return ConversationHandler.END


def list_my_wishes(update: Update, ctx: CallbackContext):
    if not ctx.user_data['wishes']['created']:
        update.message.reply_text('Вы ещё не загадали ни одного желания')
        return

    ctx.user_data['list_wish_msg_id'] = {}

    for wish_id in ctx.user_data['wishes']['created']:
        # TODO: убирать если исполнено, рисовать песочные часы или галочку
        # дать возможность пометить как выполненное
        kbd = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton('Удалить',
                                 callback_data=f'{drop_wish_inline_btn} {wish_id}')
        )
        wish = ctx.bot_data['wishes'][wish_id]
        msg = update.message.reply_text(wish['text'], reply_markup=kbd)
        ctx.user_data['list_wish_msg_id'][wish_id] = msg.message_id
    return ConversationHandler.END


@log
def remove_wish_handler(update: Update, ctx: CallbackContext):
    wish_id = int(update.callback_query.data.split(' ')[1])
    chat_id = update.effective_chat.id
    msg_id = ctx.user_data['list_wish_msg_id'][wish_id]
    ctx.bot.delete_message(chat_id, msg_id)

    ctx.user_data['wishes']['created'].remove(wish_id)
    wish = ctx.bot_data['wishes'][wish_id]
    if wish['status'] == IN_PROGRESS:
        fulfiller_data = ctx.dispatcher.user_data.get(wish['fulfiller_id'])
        fulfiller_data['wishes']['in_progress'].remove(wish_id)
    wish['status'] = REMOVED


@log
def select_wish(update: Update, ctx: CallbackContext):
    if not ctx.bot_data['wishes']:
        update.message.reply_text('Пока никто не загадал ни одного желания')
        return
    if len(ctx.user_data['wishes']['in_progress']) >= 3:
        update.message.reply_text(
            'Нельзя взять больше трёх желаний одновременно')
        return
    # Если ни одного желния не выводится -- пиать что нет желаний
    ctx.user_data['select_wish_msg_id'] = []
    chat_id = update.effective_chat.id
    for wish in ctx.bot_data['wishes'].values():
        if wish['creator_id'] == chat_id or wish['status'] != WAITING:
            continue
        kbd = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton('Взять',
                                 callback_data=f"{take_wish_inline_btn} {wish['wish_id']}")
        )
        msg = update.message.reply_text(wish['text'], reply_markup=kbd,
                                        disable_notification=True)
        ctx.user_data['select_wish_msg_id'].append(msg.message_id)


@log
def take_wish_handler(update: Update, ctx: CallbackContext):
    wish_id = int(update.callback_query.data.split(' ')[1])
    chat_id = update.effective_chat.id

    for msg_id in ctx.user_data['select_wish_msg_id']:
        ctx.bot.delete_message(chat_id, msg_id)

    wish = ctx.bot_data['wishes'][wish_id]
    wish['status'] = IN_PROGRESS
    wish['fulfiller_id'] = chat_id

    ctx.user_data['wishes']['in_progress'].append(wish_id)

    creator_data = ctx.dispatcher.user_data.get(wish['creator_id'])
    creator_name, creator_phone = creator_data['contact']

    text = f"\N{Genie}Поздравляю, теперь вы джинн😉\nЖелание:\n{wish['text']}\n\n" \
           f"Ваш Алладин:\n{creator_name} \N{em dash} {creator_phone}"
    ctx.bot.send_message(chat_id, text)
    ctx.bot.send_message(
        wish['creator_id'], "Одно из ваших желаний начали исполнять...😉")


@log
def list_fulfilled(update: Update, ctx: CallbackContext):
    if not ctx.user_data['wishes']['done']:
        update.message.reply_text("Вы ещё не выполнили ни одного желания")
        return
    for wish_id in ctx.user_data['wishes']['done']:
        update.message.reply_text(ctx.bot_data['wishes'][wish_id]['text'],
                                  disable_notification=True)


@log
def list_in_progress(update: Update, ctx: CallbackContext):
    if not ctx.user_data['wishes']['in_progress']:
        update.message.reply_text("Вы ещё не взяли на себя ни одного желания")
        return

    ctx.user_data['fulfill_wish_msg_id'] = []
    for wish_id in ctx.user_data['wishes']['in_progress']:
        wish = ctx.bot_data['wishes'][wish_id]
        kbd = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton('Отправить фото',
                                 callback_data=f'{fulfill_wish_inline_btn} {wish_id}')
        )
        creator_data = ctx.dispatcher.user_data.get(wish['creator_id'])
        creator_name, creator_phone = creator_data['contact']

        msg_text = f"{wish['text']}\n{creator_name} \N{em dash} {creator_phone}"
        msg = update.message.reply_text(msg_text, reply_markup=kbd,
                                        disable_notification=True)
        ctx.user_data['fulfill_wish_msg_id'].append(msg.message_id)


@log
def fulfill_wish_handler(update: Update, ctx: CallbackContext):
    wish_id = int(update.callback_query.data.split(' ')[1])
    chat_id = update.effective_chat.id

    for msg_id in ctx.user_data['fulfill_wish_msg_id']:
        ctx.bot.delete_message(chat_id, msg_id)

    ctx.bot.send_message(chat_id, '\N{Genie}Жду подтверждение выполненного желания')
    ctx.user_data['wish_waiting_for_proof'] = wish_id

    return WAITING_FOR_PROOF


@log
def proof_handler(update: Update, ctx: CallbackContext):
    if not update.message.photo and not update.message.video:
        update.message.reply_text('Отправьте фото или видео')
        return WAITING_FOR_PROOF
    wish_id = ctx.user_data['wish_waiting_for_proof']
    wish = ctx.bot_data['wishes'][wish_id]
    wish['status'] = DONE
    ctx.user_data['wishes']['done'].append(wish_id)
    ctx.user_data['wishes']['in_progress'].remove(wish_id)
    # TODO: сохранить фото и как-то перекинуть Артуру
    update.message.forward(ARTHUR_ID)
    ctx.bot.send_message(ARTHUR_ID, wish)
    update.message.reply_text('Желание выполнено👍')
    return ConversationHandler.END


@log
def button_handler(update: Update, ctx: CallbackContext):
    text = update.message.text
    if text == toplevel_buttons[MAKE_WISH]:
        update.message.reply_text("\N{Genie}Отправь мне своё желание")
        return MAKE_WISH
    elif text == toplevel_buttons[SELECT_WISH]:
        select_wish(update, ctx)
        return ConversationHandler.END
    elif text == toplevel_buttons[FULFILLED_LIST]:
        list_fulfilled(update, ctx)
        return ConversationHandler.END
    elif text == toplevel_buttons[WISHES_IN_PROGRESS]:
        list_in_progress(update, ctx)
        return ConversationHandler.END
    elif text == toplevel_buttons[MY_WISHES]:
        list_my_wishes(update, ctx)
        return ConversationHandler.END
