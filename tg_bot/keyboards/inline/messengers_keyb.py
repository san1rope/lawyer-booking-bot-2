from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.keyboards.inline.callback_data import temp_callback as tc

messengers_keyboard = InlineKeyboardMarkup(
    row_width=2,
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Telegram", callback_data=tc.new(title="messengers", name="telegram")),
            InlineKeyboardButton(text="WhatsApp", callback_data=tc.new(title="messengers", name="whatsapp"))
        ],
        [
            InlineKeyboardButton(text="Viber", callback_data=tc.new(title="messengers", name="viber")),
            InlineKeyboardButton(text="Письменно", callback_data=tc.new(title="messengers", name="appeal"))
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=tc.new(title="messengers", name="back"))
        ]
    ]
)
