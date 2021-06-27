intro_msg = """Добро пожаловать в пещеру Джина!\N{Genie}
Тут можно загадать своё желание
или исполнить чужое!"""

down_finger = "\N{White Down Pointing Backhand Index}"

start_msg = f"""Привет! Давай познакомимся😉\n
{down_finger}Нажми на кнопку внизу{down_finger}"""


# Buttons(int, Enum):
MAKE_WISH = 0
SELECT_WISH = 1
FULFILLED_LIST = 2
WISHES_IN_PROGRESS = 3
MY_WISHES = 4


toplevel_buttons = {
    MAKE_WISH: "Загадать желание\N{Shooting Star}",
    SELECT_WISH: "Исполнить желание",
    FULFILLED_LIST: "Список исполненных",
    WISHES_IN_PROGRESS: "Взято к выполнению",
    MY_WISHES: "Мои желания",
}

cancel_wish_making = "Отмена"

request_contact_text = "Отправить контакт\N{Mobile Phone}"

default_handler_text = (
    "Чтобы начать выбери одну из кнопок внизу\n"
    "Или отправь команду /start чтобы познакомиться заново"
)

error_text = "Что-то пошло не так😅\n" "Служба поддержки уже внимательно изучает ошибку🙏"

waiting_for_wish = "\N{Genie}Отправь мне своё желание"

no_self_wishes = "Вы ещё не выполнили ни одного желания"
no_self_created_wishes = "Вы ещё не загадали ни одного желания"

lock_and_load = "Слушаюсь и повинуюсь"

wish_limit_str = "Нельзя взять больше трёх желаний одновременно"

wish_taken = (
    "\N{Genie}Поздравляю, теперь вы джинн😉\nЖелание:\n{wish_text}\n\n"
    "Ваш Алладин:\n{creator_name} \N{em dash} {creator_phone}"
)
magick_begins = "Одно из ваших желаний начали исполнять...😉"

drop_wish_inline_btn = "drop_wish_inline_btn"
take_wish_inline_btn = "take_wish_inline_btn"
fulfill_wish_inline_btn = "fulfill_wish_inline_btn"


# class WishStatus(int, Enum):
WAITING = 5
IN_PROGRESS = 6
DONE = 7
REMOVED = 8


WAITING_FOR_PROOF = 9

ARTHUR_ALL_WISHES = 10

admin_buttons = {ARTHUR_ALL_WISHES: "Админ: список всех желаний"}

WISHES_TO_SHOW_LIMIT = 5
