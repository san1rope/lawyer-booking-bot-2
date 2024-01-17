import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import ChatTypeFilter, Text, Command
from aiogram.utils.markdown import hcode

from tg_bot.config import Config
from tg_bot.keyboards.inline.contacts_keyb import contacts_keyboard
from tg_bot.misc.data_handling import bot_commands

logger = logging.getLogger(__name__)


async def show_contacts(message: types.Message):
    logger.info(f"Handler called. {show_contacts.__name__}. user_id={message.from_user.id}")

    await message.answer(text="<b>Посетите страницы в соцсетях ⬇️</b>", reply_markup=contacts_keyboard)


async def show_phone_number(callback: types.CallbackQuery):
    logger.info(f"Handler called. {show_phone_number.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    await callback.message.answer_contact(phone_number=Config.CONTACTS_PHONE_NUMBER,
                                          first_name=Config.CONTACTS_FIRST_NAME)


async def show_office_location(callback: types.CallbackQuery):
    logger.info(f"Handler called. {show_office_location.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    text = [
        "<b>Адрес офиса:</b>\n",
        hcode(Config.CONTACTS_ADDRESS)
    ]

    message = callback.message
    await message.answer(text='\n'.join(text))
    await message.answer_location(latitude=Config.CONTACTS_OFFICE_LATITUDE, longitude=Config.CONTACTS_OFFICE_LONGITUDE)


async def show_email(callback: types.CallbackQuery):
    logger.info(f"Handler called. {show_email.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    text = [
        "<b>Электронная почта:</b>\n",
        hcode(Config.CONTACTS_EMAIL)
    ]

    message = callback.message
    await message.answer(text='\n'.join(text))


def register_contacts(dp: Dispatcher):
    dp.register_message_handler(show_contacts, ChatTypeFilter(types.ChatType.PRIVATE),
                                Text(bot_commands.get("/contacts")) | Command('contacts'))
    dp.register_callback_query_handler(show_phone_number, text="contacts_phone_number")
    dp.register_callback_query_handler(show_office_location, text="contacts_office_location")
    dp.register_callback_query_handler(show_email, text="contacts_email")
