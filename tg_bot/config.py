from typing import List

import pytz
import os

from aiogram import Bot
from aiogram.types import ParseMode
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    BOT: Bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    ADMINS: List[int] = [int(admin_id) for admin_id in os.getenv("ADMINS").strip().split(',')]
    TIMEZONE = pytz.timezone(os.getenv("TIMEZONE"))

    MAX_RECORDS_PER_USER: int = int(os.getenv("MAX_RECORDS_PER_USER"))
    MAX_APPEALS_PER_USER: int = int(os.getenv("MAX_APPEALS_PER_USER"))
    RECORD_MONITORING_DELAY: float = float(os.getenv("RECORD_MONITORING_DELAY"))

    CONTACTS_FACEBOOK_URL: str = os.getenv("CONTACTS_FACEBOOK_URL")
    CONTACTS_INSTAGRAM_URL: str = os.getenv("CONTACTS_INSTAGRAM_URL")
    CONTACTS_TELEGRAM_URL: str = os.getenv("CONTACTS_TELEGRAM_URL")
    CONTACTS_PHONE_NUMBER: str = os.getenv("CONTACTS_PHONE_NUMBER")
    CONTACTS_FIRST_NAME: str = os.getenv("CONTACTS_FIRST_NAME")
    CONTACTS_ADDRESS: str = os.getenv("CONTACTS_ADDRESS")
    CONTACTS_EMAIL: str = os.getenv("CONTACTS_EMAIL")
    CONTACTS_OFFICE_LATITUDE: float = float(os.getenv("CONTACTS_OFFICE_LATITUDE"))
    CONTACTS_OFFICE_LONGITUDE: float = float(os.getenv("CONTACTS_OFFICE_LONGITUDE"))

    PAYMENT_URL: str = os.getenv("PAYMENT_URL")
