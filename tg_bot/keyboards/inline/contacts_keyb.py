from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.config import Config

contacts_keyboard = InlineKeyboardMarkup(row_width=2,
                                         inline_keyboard=[
                                             [
                                                 InlineKeyboardButton(text="Геолокация офиса",
                                                                      callback_data="contacts_office_location"),

                                                 InlineKeyboardButton(text="Telegram",
                                                                      url=Config.CONTACTS_TELEGRAM_URL,
                                                                      callback_data="contacts_telegram")
                                             ],
                                             [
                                                 InlineKeyboardButton(text="Facebook",
                                                                      url=Config.CONTACTS_FACEBOOK_URL,
                                                                      callback_data="contacts_facebook"),
                                                 InlineKeyboardButton(text="Instagram",
                                                                      url=Config.CONTACTS_INSTAGRAM_URL,
                                                                      callback_data="contacts_instagram")
                                             ]
                                         ])
