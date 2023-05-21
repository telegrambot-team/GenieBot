from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler, ChatMemberHandler,
)

from src.base_handlers import (
    start_handler,
    default_handler,
    ups_handler,
    drop_wish,
    restricted,
)
from src.button_handlers import (
    button_handler,
    make_wish_handler,
    incorrect_wish_handler,
    remove_wish_handler,
    take_wish_handler,
    fulfill_wish_handler,
    proof_handler,
    cancel_wish_making_handler,
    control_list_wish_handler,
)
import src.constants as constants
from src.chat_track_handler import greet_chat_members


def setup_handlers(updater, admin_ids: list[int]):
    dispatcher = updater.dispatcher
    persist = updater.persistence is not None
    dispatcher.add_handler(CommandHandler("start", start_handler))
    dispatcher.add_handler(CommandHandler("dropwish", restricted(drop_wish, admin_ids)))
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    Filters.text(
                        list(constants.toplevel_buttons.values())
                        + list(constants.admin_buttons.values())
                    ),
                    button_handler,
                )
            ],
            states={
                constants.MAKE_WISH: [
                    MessageHandler(
                        Filters.text([constants.cancel_wish_making]),
                        cancel_wish_making_handler,
                    ),
                    MessageHandler(Filters.text, make_wish_handler),
                    MessageHandler(Filters.chat_type.private, incorrect_wish_handler),
                ]
            },
            fallbacks=[],
            persistent=persist,
            name="ButtonsHandler",
            per_chat=False,
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            remove_wish_handler, pattern=f"^{constants.drop_wish_inline_btn}.*"
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            take_wish_handler, pattern=f"^{constants.take_wish_inline_btn}.*\\d+"
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            control_list_wish_handler, pattern=f"^{constants.take_wish_inline_btn}.*"
        )
    )
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    fulfill_wish_handler,
                    pattern=f"^{constants.fulfill_wish_inline_btn}.*",
                )
            ],
            states={
                constants.WAITING_FOR_PROOF: [
                    MessageHandler(Filters.chat_type.private, proof_handler)
                ]
            },
            fallbacks=[],
            persistent=persist,
            name="ProofHandler",
            per_chat=False,
        )
    )

    dispatcher.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    dispatcher.add_handler(MessageHandler(Filters.chat_type.private, default_handler))

    dispatcher.add_error_handler(ups_handler)
