from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from tg_bot.config import Config
from tg_bot.misc.data_handling import bot_commands


def start_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(text=bot_commands.get("/filling"))
            ],
            [
                KeyboardButton(text=bot_commands.get("/contacts")),
                KeyboardButton(text=bot_commands.get("/common_questions")),
                KeyboardButton(text=bot_commands.get("/records"))
            ],
            [
                KeyboardButton(text=bot_commands.get("/appeals"))
            ]
        ]
    )

    if user_id in Config.ADMINS:
        button = KeyboardButton(bot_commands.get("/apanel"))
        markup.row(button)

    return markup
