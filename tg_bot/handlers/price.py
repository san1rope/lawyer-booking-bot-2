from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hcode

from tg_bot.misc.utils import add_msg_to_delete


async def show_price(callback: types.CallbackQuery):
    await callback.answer()

    text = [
        "<b>Прайс 📋</b>",
        f"\nУслуга - <b>Онлайн консультация</b>",
        f"Стоимость: {hcode('800')} грн. Время: 40 мин.",
        f"\nУслуга - <b>Консультация в офисе</b>",
        f"Стоимость: {hcode('1000')} грн. Время: 40 мин."
    ]
    markup = InlineKeyboardMarkup(row_width=1,
                                  inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_price")]])
    msg = await callback.message.edit_text('\n'.join(text), reply_markup=markup)
    add_msg_to_delete(user_id=callback.from_user.id, msg_id=msg.message_id)


def register_menu_price(dp: Dispatcher):
    dp.register_callback_query_handler(show_price, ChatTypeFilter(types.ChatType.PRIVATE), text="price")
