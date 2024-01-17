import types
from datetime import timedelta
from typing import Optional, Union

from aiogram import Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted
from aiogram.utils.markdown import hcode

from tg_bot.config import Config
from tg_bot.misc.data_handling import msg_to_delete, all_records, timeline, amount_time_per_service, reminder


def form_completion(title: str, end: str = '', record_data: Optional[dict] = None) -> str:
    if record_data:
        service = record_data.get("service")
        date = record_data.get("date")
        time = record_data.get("time")
        number = record_data.get("number")
        name = record_data.get("name")
        text = record_data.get("text")
    else:
        service, date, time, number, name, text = None, None, None, None, None, None

    r_text = [
        f"<b>{title}</b>",
        f"{hcode('Услуга:')} {service if service else ''}",
        f"{hcode('Дата:')} {date if date else ''}",
        f"{hcode('Время:')} {time if time else ''}",
        f"{hcode('Телефон:')} {number if number else ''}",
        hcode('Имя: ') + str(name if name else '')
    ]
    if record_data and record_data.get("messenger"):
        r_text.insert(2, f"{hcode('Месенджер:')} {record_data.get('messenger')}")

    if text:
        r_text.append(f"{hcode('Текст: ')} {text}")

    r_text.append(end)

    return '\n\n'.join(r_text)


def add_msg_to_delete(user_id: int, msg_id: int):
    if user_id not in msg_to_delete:
        msg_to_delete[user_id] = []

    msg_to_delete[user_id].append(msg_id)


async def delete_messages(user_id: Optional[int] = None):
    try:
        if not user_id:
            for uid in msg_to_delete:
                for msg_id in msg_to_delete.get(uid):
                    try:
                        print(2)
                        await Bot.get_current().delete_message(chat_id=uid, message_id=msg_id)
                    except (MessageToDeleteNotFound, MessageCantBeDeleted):
                        continue

            return

        for msg_id in msg_to_delete[user_id]:
            try:
                await Bot.get_current().delete_message(chat_id=user_id, message_id=msg_id)
            except (MessageToDeleteNotFound, MessageCantBeDeleted):
                continue

        msg_to_delete[user_id].clear()
    except KeyError:
        return


def remove_record(user_id: str, record_index: str):
    date = all_records[user_id][record_index]["date"].split('.')
    time = all_records[user_id][record_index]["time"].split(':')
    day, month, year = date[0], date[1], date[2]

    time_amount_split = amount_time_per_service.get(all_records[user_id][record_index]["service"]).split(':')
    will_take_time_ = timedelta(hours=int(time_amount_split[0]), minutes=int(time_amount_split[1]))
    time_start = timedelta(hours=int(time[0]), minutes=int(time[1]))
    time_end = time_start + will_take_time_
    while time_start != time_end:
        print(f"remove_record: time_start: {time_start}; record_index: {record_index}")
        time_start_ = str(time_start).split(':')
        time_str = f"{time_start_[0]}:{time_start_[1]}"
        if time_start > timedelta(hours=19):
            break

        timeline[time_str][year][month].pop(day)
        if len(timeline[time_str][year][month]) == 0:
            timeline[time_str][year].pop(month)
            if len(timeline[time_str][year]) == 0:
                timeline[time_str].pop(year)

        time_start += timedelta(hours=1)

    all_records[user_id].pop(record_index)
    if len(all_records[user_id]) == 0:
        all_records.pop(user_id)

    if (user_id in reminder) and (record_index in reminder[user_id]):
        reminder[user_id].pop(record_index)
        if not reminder[user_id]:
            reminder.pop(user_id)


async def send_record(title: str, record: dict, uid: str, end: str = '', edit: Message = None,
                      reply_markup: Union[
                          ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove] = None) -> Message:
    text = form_completion(title=title, end=end, record_data=record)
    file_id = record.get("file_id")
    if file_id:
        file_type = record.get("file_type")

        if file_type == "photo":
            return await Config.BOT.send_photo(chat_id=uid, photo=file_id, caption=text, reply_markup=reply_markup)
        elif file_type == "video":
            return await Config.BOT.send_video(chat_id=uid, video=file_id, caption=text, reply_markup=reply_markup)
        elif file_type == "document":
            return await Config.BOT.send_document(chat_id=uid, document=file_id, caption=text,
                                                  reply_markup=reply_markup)
    else:
        if edit:
            try:
                return await edit.edit_text(text=text, reply_markup=reply_markup,
                                            disable_web_page_preview=True)
            except Exception:
                pass

        return await Config.BOT.send_message(chat_id=uid, text=text, reply_markup=reply_markup,
                                             disable_web_page_preview=True)
