from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
)

from src.base_handlers import (
    start_handler,
    contact_handler,
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
)
from src.constants import (
    toplevel_buttons,
    admin_buttons,
    MAKE_WISH,
    drop_wish_inline_btn,
    take_wish_inline_btn,
    fulfill_wish_inline_btn,
    WAITING_FOR_PROOF,
)


def setup_handlers(updater, admin_ids: list[int]):
    dispatcher = updater.dispatcher
    persist = updater.persistence is not None
    dispatcher.add_handler(CommandHandler("start", start_handler))
    dispatcher.add_handler(CommandHandler("dropwish", restricted(drop_wish, admin_ids)))
    dispatcher.add_handler(MessageHandler(Filters.contact, contact_handler))
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    Filters.text(
                        list(toplevel_buttons.values()) + list(admin_buttons.values())
                    ),
                    button_handler,
                )
            ],
            states={
                MAKE_WISH: [
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
        CallbackQueryHandler(remove_wish_handler, pattern=f"^{drop_wish_inline_btn}.*")
    )
    dispatcher.add_handler(
        CallbackQueryHandler(take_wish_handler, pattern=f"^{take_wish_inline_btn}.*")
    )
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    fulfill_wish_handler, pattern=f"^{fulfill_wish_inline_btn}.*"
                )
            ],
            states={
                WAITING_FOR_PROOF: [
                    MessageHandler(Filters.chat_type.private, proof_handler)
                ]
            },
            fallbacks=[],
            persistent=persist,
            name="ProofHandler",
            per_chat=False,
        )
    )
    dispatcher.add_handler(MessageHandler(Filters.chat_type.private, default_handler))

    dispatcher.add_error_handler(ups_handler)
