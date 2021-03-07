intro_msg = '''Добро пожаловать в пещеру Джина!\N{Genie}
Тут можно загадать своё желание
или исполнить чужое!'''

down_finger = "\N{White Down Pointing Backhand Index}"

start_msg = f'''Привет! Давай познакомимся😉\n
{down_finger}Нажми на кнопку внизу{down_finger}'''


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
    MY_WISHES: "Мои желания"
}


request_contact_text = "Отправить контакт\N{Mobile Phone}"

default_handler_text = "Чтобы начать выбери одну из кнопок внизу\n" \
                       "Или отправь команду /start чтобы познакомиться заново"

error_text = 'Что-то пошло не так😅\n' \
             'Служба поддержки уже внимательно изучает ошибку🙏'

drop_wish_inline_btn = 'drop_wish_inline_btn'
take_wish_inline_btn = 'take_wish_inline_btn'
fulfill_wish_inline_btn = 'fulfill_wish_inline_btn'


# class WishStatus(int, Enum):
WAITING = 5
IN_PROGRESS = 6
DONE = 7
REMOVED = 8


WAITING_FOR_PROOF = 9

ADMIN_ALL_WISHES = 10

admin_buttons = {
    ADMIN_ALL_WISHES: 'Админ: список всех желаний'
}
