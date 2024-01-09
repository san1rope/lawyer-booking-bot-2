from typing import Union

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.keyboards.inline.callback_data import temp_callback as tc


def remove_confirm(name: Union[str, dict, list], title_arg: str = "agreement") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2,
                                inline_keyboard=[
                                    [
                                        InlineKeyboardButton(text="Подтверждаю",
                                                             callback_data=tc.new(title=title_arg, name=name)),
                                        InlineKeyboardButton(text="Отказываюсь",
                                                             callback_data=tc.new(title=title_arg, name="disagree"))
                                    ]
                                ])
