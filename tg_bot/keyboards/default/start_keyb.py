from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from tg_bot.config import Config

title_start_recording = "Записаться на консультацию"
title_contacts = "Контакты"
title_common_questions = "Частые вопросы"
title_records = "Записи"
title_appeals = "Обращения"


def start_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(text=title_start_recording)
            ],
            [
                KeyboardButton(text=title_contacts),
                KeyboardButton(text=title_common_questions),
                KeyboardButton(text=title_records)
            ],
            [
                KeyboardButton(text=title_appeals)
            ]
        ]
    )

    if user_id in Config.ADMINS:
        button = KeyboardButton("Меню администратора")
        markup.row(button)

    return markup
