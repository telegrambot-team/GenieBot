from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.bot import log
from telegram.ext import CallbackContext, ConversationHandler

from src.base_handlers import start_handler
from src.config import get_config
from src.constants import toplevel_buttons, WAITING_FOR_PROOF, MAKE_WISH, \
    SELECT_WISH, FULFILLED_LIST, WISHES_IN_PROGRESS, MY_WISHES, WAITING, REMOVED, IN_PROGRESS, drop_wish_inline_btn, \
    fulfill_wish_inline_btn, take_wish_inline_btn, DONE, admin_buttons, ADMIN_ALL_WISHES, waiting_for_wish, \
    no_self_wishes, lock_and_load, no_self_created_wishes, wish_taken, magick_begins


def incorrect_wish_handler(update: Update, _: CallbackContext):
    update.message.reply_text("Я только читать умею, ты текстом пиши")
    return MAKE_WISH


def make_wish_handler(update: Update, ctx: CallbackContext):
    if update.message.text in toplevel_buttons.values():
        update.message.reply_text("Будем считать это случайностью\N{Winking Face}")
        return MAKE_WISH

    wish_id = len(ctx.bot_data['wishes'])
    new_wish = {
        'wish_id': wish_id,
        'creator_id': update.effective_user.id,
        'text': update.message.text,
        'fulfiller_id': None,
        'status': WAITING,
        'proof_msg_id': None
    }
    # str is used because of storing dict as json; json can not have int keys
    ctx.bot_data['wishes'][str(wish_id)] = new_wish
    ctx.user_data['wishes']['created'].append(wish_id)

    update.message.reply_text(lock_and_load)
    return ConversationHandler.END


def list_my_wishes(update: Update, ctx: CallbackContext):
    if not ctx.user_data['wishes']['created']:
        update.message.reply_text(no_self_created_wishes)
        return

    ctx.user_data['list_wish_msg_id'] = {}

    for wish_id in ctx.user_data['wishes']['created']:
        wish = ctx.bot_data['wishes'][str(wish_id)]
        if wish['status'] == WAITING:
            kbd = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton('Удалить',
                                     callback_data=f'{drop_wish_inline_btn} {wish_id}')
            )
        elif wish['status'] == IN_PROGRESS:
            kbd = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton('Выполняется'
                                     '\N{Hourglass with Flowing Sand}',
                                     callback_data='pass')
            )
        elif wish['status'] == DONE:
            kbd = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton('Выполнено'
                                     '\N{White Heavy Check Mark}',
                                     callback_data='pass')
            )
        else:
            raise RuntimeError(f"Invalid wish status {wish['status']}")
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
    wish = ctx.bot_data['wishes'][str(wish_id)]
    if wish['status'] == IN_PROGRESS:
        fulfiller_data = ctx.dispatcher.user_data.get(wish['fulfiller_id'])
        fulfiller_data['wishes']['in_progress'].remove(wish_id)
    wish['status'] = REMOVED


@log
def select_wish(update: Update, ctx: CallbackContext):
    if len(ctx.user_data['wishes']['in_progress']) >= 3:
        update.message.reply_text(
            'Нельзя взять больше трёх желаний одновременно')
        return
    ctx.user_data['select_wish_msg_id'] = []
    chat_id = update.effective_chat.id

    counter = 0

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
        counter += 1

    if counter == 0:
        update.message.reply_text('Пока нет желаний для выполнения')


@log
def take_wish_handler(update: Update, ctx: CallbackContext):
    wish_id = int(update.callback_query.data.split(' ')[1])
    chat_id = update.effective_chat.id

    for msg_id in ctx.user_data['select_wish_msg_id']:
        ctx.bot.delete_message(chat_id, msg_id)

    wish = ctx.bot_data['wishes'][str(wish_id)]
    wish['status'] = IN_PROGRESS
    wish['fulfiller_id'] = chat_id

    ctx.user_data['wishes']['in_progress'].append(wish_id)

    creator_data = ctx.dispatcher.user_data.get(wish['creator_id'])
    creator_name, creator_phone = creator_data['contact']

    text = wish_taken.format(wish_text=wish['text'], creator_name=creator_name,
                             creator_phone=creator_phone)
    ctx.bot.send_message(chat_id, text)
    ctx.bot.send_message(
        wish['creator_id'], magick_begins)


@log
def list_fulfilled(update: Update, ctx: CallbackContext):
    if not ctx.user_data['wishes']['done']:
        update.message.reply_text(no_self_wishes)
        return
    for wish_id in ctx.user_data['wishes']['done']:
        wish_text = ctx.bot_data['wishes'][str(wish_id)]['text']
        creator_data = ctx.dispatcher.user_data.get(ctx.bot_data['wishes'][str(wish_id)]['creator_id'])
        creator_name, creator_phone = creator_data['contact']
        msg_text = f'{wish_text}\n{creator_name} \N{em dash} {creator_phone}'
        update.message.reply_text(msg_text,
                                  disable_notification=True)


@log
def list_in_progress(update: Update, ctx: CallbackContext):
    if not ctx.user_data['wishes']['in_progress']:
        update.message.reply_text("Вы ещё не взяли на себя ни одного желания")
        return

    ctx.user_data['fulfill_wish_msg_id'] = []
    for wish_id in ctx.user_data['wishes']['in_progress']:
        wish = ctx.bot_data['wishes'][str(wish_id)]
        assert wish['status'] == IN_PROGRESS
        kbd = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton('Отправить фото или видео',
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

    ctx.bot.send_message(chat_id, '\N{Genie}Жду подтверждение выполненного желания.\n'
                                  'Отправь фото или видео\N{Winking Face}')
    ctx.user_data['wish_waiting_for_proof'] = wish_id

    return WAITING_FOR_PROOF


@log
def proof_handler(update: Update, ctx: CallbackContext):
    if not update.message.photo and not update.message.video:
        update.message.reply_text('Отправьте фото или видео')
        return WAITING_FOR_PROOF
    wish_id = ctx.user_data['wish_waiting_for_proof']
    wish = ctx.bot_data['wishes'][str(wish_id)]
    wish['status'] = DONE
    wish['proof_msg_id'] = update.message.message_id
    ctx.user_data['wishes']['done'].append(wish_id)
    ctx.user_data['wishes']['in_progress'].remove(wish_id)
    update.message.reply_text('Желание исполнено👍')

    creator_id = wish['creator_id']
    ctx.bot.forward_message(creator_id, wish['fulfiller_id'], wish['proof_msg_id'])
    ctx.bot.send_message(creator_id, 'Желание исполнено👍')
    return ConversationHandler.END


@log
def admin_list_all_wishes(update: Update, ctx: CallbackContext):
    conf = get_config()
    for wish in ctx.bot_data['wishes'].values():
        if wish['status'] != DONE:
            continue

        creator_data = ctx.dispatcher.user_data.get(wish['creator_id'])
        creator_name, creator_phone = creator_data['contact']

        msg_text = f"{wish['text']}\n{creator_name} \N{em dash} {creator_phone}"
        update.message.reply_text(msg_text)
        ctx.bot.forward_message(conf.arthur_id, wish['fulfiller_id'], wish['proof_msg_id'])


@log
def button_handler(update: Update, ctx: CallbackContext):
    if 'contact' not in ctx.user_data:
        start_handler(update, ctx)
        return
    text = update.message.text
    if text == toplevel_buttons[MAKE_WISH]:
        update.message.reply_text(waiting_for_wish)
        return MAKE_WISH
    elif text == toplevel_buttons[SELECT_WISH]:
        select_wish(update, ctx)
        return ConversationHandler.END
    elif text == toplevel_buttons[FULFILLED_LIST]:
        # TODO: add pagination
        list_fulfilled(update, ctx)
        return ConversationHandler.END
    elif text == toplevel_buttons[WISHES_IN_PROGRESS]:
        # TODO: add pagination
        list_in_progress(update, ctx)
        return ConversationHandler.END
    elif text == toplevel_buttons[MY_WISHES]:
        # TODO: add pagination
        list_my_wishes(update, ctx)
        return ConversationHandler.END
    # TODO: and if sender is admin
    elif text == admin_buttons[ADMIN_ALL_WISHES]:
        admin_list_all_wishes(update, ctx)
        return ConversationHandler.END
