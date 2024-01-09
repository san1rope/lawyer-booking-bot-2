from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.keyboards.inline.callback_data import temp_callback as tc


def remove_inline(name: str, title: str, title_arg: str = "remove"):
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [InlineKeyboardButton(text=title, callback_data=tc.new(title=title_arg, name=name))]])
