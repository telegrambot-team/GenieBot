from enum import Enum, auto

intro_msg = '''Добро пожаловать в пещеру Джина!\N{Genie}
Тут можно загадать своё желание
или исполнить чужое!'''

start_msg = '''Привет! Давай познакомимся😉\n
Нажми на кнопку внизу, чтобы отправить мне свой номер телефона'''


class Buttons(int, Enum):
    MAKE_WISH = auto()
    FULFILL_WISH = auto()
    FULFILLED_LIST = auto()
    TODO_WISHES = auto()
    MY_WISHES = auto()


toplevel_buttons = {
    Buttons.MAKE_WISH: "Загадать желание\N{Shooting Star}",
    Buttons.FULFILL_WISH: "Исполнить желание",
    Buttons.FULFILLED_LIST: "Список исполненных",
    Buttons.TODO_WISHES: "Взято к выполнению",
    Buttons.MY_WISHES: "Мои желания"
}

request_contact_text = "Отправить\N{Mobile Phone}"

default_handler_text = "Чтобы начать выбери одну из кнопок внизу"

error_text = 'Что-то пошло не так😅\n'\
             'Служба поддержки уже внимательно изучает ошибку🙏'
