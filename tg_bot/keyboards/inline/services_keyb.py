from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.keyboards.inline.callback_data import temp_callback as tc

services_keyboard = InlineKeyboardMarkup(
    row_width=2,
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Онлайн консультация",
                                 callback_data=tc.new(title="service",
                                                      name="online_consultation")),
            InlineKeyboardButton(text="Консультация в офисе",
                                 callback_data=tc.new(title="service",
                                                      name="office_consultation"))
        ],
        [
            InlineKeyboardButton(text="Прайс", callback_data="price")
        ]
    ]
)
