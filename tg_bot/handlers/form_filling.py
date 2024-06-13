import logging
from datetime import datetime, timedelta
from typing import Union

from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, Text, Command
from aiogram.utils.exceptions import ChatNotFound, BotBlocked, MessageToEditNotFound
from aiogram.utils.markdown import hcode

from tg_bot.config import Config
from tg_bot.handlers.admin.panel import cmd_panel
from tg_bot.handlers.common_questions import show_questions
from tg_bot.handlers.contacts import show_contacts
from tg_bot.handlers.records import show_records
from tg_bot.handlers.show_appeals import show_user_appeals
from tg_bot.handlers.start import cmd_start
from tg_bot.keyboards.default.start_keyb import start_keyboard
from tg_bot.keyboards.inline.back_keyb import back_keyboard
from tg_bot.keyboards.inline.callback_data import temp_callback as tc, calendar_callback as cc, time_callback as tcb
from tg_bot.keyboards.inline.date_keyb import calendar_keyboard
from tg_bot.keyboards.default.payment_keyb import payment_keyboard
from tg_bot.keyboards.inline.messengers_keyb import messengers_keyboard
from tg_bot.keyboards.inline.paid_keyb import paid_keyboard
from tg_bot.keyboards.inline.services_keyb import services_keyboard, add_appeal_keyboard
from tg_bot.keyboards.inline.time_keyb import time_keyboard
from tg_bot.misc.data_handling import services, service_prices, all_records, amount_time_per_service, timeline, \
    reminder, appeals, bot_commands, online_consultation
from tg_bot.misc.states import ProvideContacts, SendAppeal, AddAppealToRecord
from tg_bot.misc.utils import delete_messages, add_msg_to_delete, send_record

logger = logging.getLogger(__name__)

temp_records, temp_callback_data, msg_state_id = {}, {}, {}
temp_year, temp_month, temp_day = {}, {}, {}


async def start_filling(message: Union[types.Message, types.CallbackQuery], edit_message: bool = False, text: str = ''):
    logger.info(f"Handler called. {start_filling.__name__}. user_id={message.from_user.id}")

    uid = message.from_user.id
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message

    await delete_messages(uid)

    if (str(uid) in all_records) and (len(all_records[str(uid)]) >= Config.MAX_RECORDS_PER_USER):
        await message.answer(
            text=f"<b>Не удалось начать запись\nВы уже имеете записей: {Config.MAX_RECORDS_PER_USER}</b>")
        return

    if uid in temp_records:
        temp_records.pop(uid)

    text = f"{text}Ознакомьтесь с прайсом, выберите формат консультации, дату и время 👇"
    if edit_message:
        await send_record(title=text, reply_markup=services_keyboard, record={}, uid=uid, edit=message)
    else:
        await send_record(title=text, uid=uid, reply_markup=services_keyboard, record={})


async def choose_service(callback: types.CallbackQuery, callback_data: dict, msg_text: str = None):
    logger.info(f"Handler called. {choose_service.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    uid = callback.from_user.id
    name = callback_data.get("name")

    if callback_data.get("title") == "messengers":
        temp_callback_data[uid].update({"messenger": callback_data})
        if name == "back":
            return await start_filling(message=callback, edit_message=True)
        elif name == "appeal":
            user_appeals = appeals.get(str(uid))
            if user_appeals and len(user_appeals) >= Config.MAX_APPEALS_PER_USER:
                text = f"<b>Не удалось создать обращение!\nУ вас есть активных обращений: {len(user_appeals)}</b>\n\n"
                return await start_filling(message=callback.message, edit_message=True, text=text)

            await delete_messages(uid)

            text = [
                "<b>Письменная консультация 📝</b>",
                "<b>Пришлите свои материалы администратору</b>",
                "<b>Можно присылать документы 📎 и медиа файлы 📷</b>"
                "<b>Информация и документы подаются за день до онлайн консультации</b>"
            ]
            markup = add_appeal_keyboard(add=False)
            markup.inline_keyboard[0].pop(0)
            msg = await callback.message.answer(text='\n'.join(text), reply_markup=markup)
            add_msg_to_delete(user_id=callback.from_user.id, msg_id=msg.message_id)
            await SendAppeal.File.set()
            return

        temp_records[uid].update({"messenger": name.capitalize()})
    else:
        temp_callback_data[uid] = {"service": callback_data}
        temp_records[uid] = {"service": services.get(name)}

        if name == "online_consultation":
            text = "Выберите мессенджер"
            return await send_record(uid=uid, title=text, reply_markup=messengers_keyboard,
                                     record=temp_records.get(uid), edit=callback.message)

    today = datetime.now(Config.TIMEZONE)
    markup = calendar_keyboard(year=today.year, month=today.month, day_=today.day)
    await send_record(title=(msg_text if msg_text else "Выберите дату"), record=temp_records.get(uid),
                      reply_markup=markup, uid=uid, edit=callback.message)


async def appeal_payment(message: Union[types.Message, types.CallbackQuery], state: FSMContext,
                         callback_data: dict = None):
    logger.info(f"Handler called. {appeal_payment.__name__}. user_id={message.from_user.id}")

    uid = message.from_user.id

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        name = callback_data.get("name")

        if name == "back":
            await state.reset_state()
            return await choose_service(callback=message, callback_data=temp_callback_data[uid].get("service"))
        elif name == "continue":
            await delete_messages(uid)

            text = f"\n\n<b>К оплате {hcode(service_prices.get(online_consultation))} грн.</b>"
            msg = await message.message.answer(text=text, reply_markup=payment_keyboard)
            add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            text = "<b>Чтобы оплатить обращение, \nнажмите внизу экрана кнопку - Перейти к оплате💳</b>"
            msg = await message.message.answer(text=text, reply_markup=paid_keyboard)
            add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

            await SendAppeal.Payment.set()
            return

    if message.text:
        msg_text = message.text.strip()
        if msg_text.startswith("/"):
            if msg_text == "/start":
                await state.reset_state()
                return await cmd_start(message)
            elif msg_text == "/records":
                await state.reset_state()
                return await show_records(message)
            elif msg_text == "/apanel":
                if uid in Config.ADMINS:
                    await state.reset_state()
                    return await cmd_panel(message)
            elif msg_text == "/filling":
                await state.reset_state()
                return await start_filling(message)
            elif msg_text == "/common_questions":
                await state.reset_state()
                return await show_questions(message)
            elif msg_text == "/contacts":
                await state.reset_state()
                return await show_contacts(message=message)
            elif msg_text == "/appeals":
                await state.reset_state()
                return await show_user_appeals(message=message)

    if message.content_type == types.ContentType.TEXT:
        appeal_files = {"text": message.text}
    elif message.content_type == types.ContentType.DOCUMENT:
        appeal_files = {"text": message.caption, "file_id": message.document.file_id, "file_type": "document"}
    elif message.content_type == types.ContentType.PHOTO:
        appeal_files = {"text": message.caption, "file_id": message.photo[0].file_id, "file_type": "photo"}
    elif message.content_type == types.ContentType.VIDEO:
        appeal_files = {"text": message.caption, "file_id": message.video.file_id, "file_type": "video"}
    else:
        return await message.answer("<b>Вы прислали неверный тип сообщения!\bПопробуйте ещё раз</b>")

    data = await state.get_data()
    if "new_appeal" in data:
        new_appeal = data["new_appeal"]
        new_appeal["files"].append(appeal_files)
        await state.update_data(new_appeal=new_appeal)
    else:
        new_appeal = {
            "id": appeals["last_id"] + 1,
            "username": message.from_user.username,
            "full_name": message.from_user.full_name,
            "files": [appeal_files]
        }
        await state.update_data(new_appeal=new_appeal)

    await delete_messages(uid)

    text = "<b>Материал сохранен!\nМожете дальше присылать информацию или продолжить</b>"
    msg = await message.answer(text=text, reply_markup=add_appeal_keyboard(add=False))
    add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


async def send_appeal(callback: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logger.info(f"Handler called. {send_appeal.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    uid = callback.from_user.id

    operation = callback_data.get("name")
    if operation == "back":
        await state.reset_state()
        return await choose_service(callback=callback, callback_data=temp_callback_data[uid].get("messenger"))
    elif operation == "confirm":
        data = await state.get_data()
        new_appeal = data["new_appeal"]

        if str(uid) in appeals:
            appeals[str(uid)].append(new_appeal)
        else:
            appeals[str(uid)] = [new_appeal]

        appeals["last_id"] += 1
        await delete_messages(uid)

        await callback.message.answer(
            f"<b>Вы добавили новое обращение №{new_appeal['id']}\nОжидайте ответа администратора.</b>",
            reply_markup=start_keyboard(uid))

        for admin_id in Config.ADMINS:
            if uid != admin_id:
                await Bot.get_current().send_message(chat_id=admin_id, text="<b>Добавлено новое обращение!</b>")

        await state.reset_state()


async def choose_date(callback: types.CallbackQuery, callback_data: dict, msg_text: str = None):
    logger.info(f"Handler called. {choose_date.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    global temp_year
    global temp_month
    global temp_day

    uid = callback.from_user.id
    arg1 = callback_data.get("arg1")
    arg2 = callback_data.get("arg2")
    today = datetime.now(Config.TIMEZONE)

    temp_callback_data[uid].update({"date": callback_data})

    if arg2 == "back":
        if "messenger" in temp_callback_data[uid]:
            print(1, temp_callback_data)
            return await choose_service(callback=callback, callback_data=temp_callback_data[uid].get("service"))

        return await start_filling(callback, edit_message=True)

    if arg2 == "unclick":
        return

    if arg1 == "day":
        year, month, day = callback_data.get("arg4"), callback_data.get("arg3"), arg2

        record_counter = 0
        for time_ in timeline:
            if (str(year) in timeline[time_]) and (str(month) in timeline[time_][str(year)]) and (
                    str(day) in timeline[time_][str(year)][str(month)]):
                record_counter += 1

        if record_counter == len(timeline):
            temp_records[uid].pop("date", None)
            text = "Нет свободного времени в этот день.\nВыберите другую дату."
            return await choose_service(callback, callback_data=temp_callback_data[uid]["service"], msg_text=text)

        temp_records[uid]["date"] = f"{day}.{month}.{year}"

        service = temp_records[uid]["service"]
        markup = time_keyboard(year=year, month=month, day=day, service=service)
        return await send_record(title=(msg_text if msg_text else "Выберите время 🕒"), reply_markup=markup, uid=uid,
                                 record=temp_records.get(uid), edit=callback.message)

    if arg1 == "move":
        if uid not in temp_year:
            temp_year[uid] = today.year
            temp_month[uid] = today.month

        if arg2 == "left":
            if temp_year[uid] == today.year:
                if temp_month[uid] == today.month:
                    temp_day[uid] = today.day
                    return
                else:
                    if (today.month + 1) == temp_month[uid]:
                        temp_day[uid] = today.day
                    if temp_month[uid] == 1:
                        temp_year[uid] -= 1
                        temp_month[uid] = 12
                    else:
                        temp_month[uid] -= 1
            else:
                if temp_month[uid] == 1:
                    temp_year[uid] -= 1
                    temp_month[uid] = 12
                else:
                    temp_month[uid] -= 1
        elif arg2 == "right":
            temp_day[uid] = 1
            if temp_month[uid] == 12:
                temp_year[uid] += 1
                temp_month[uid] = 1
            else:
                temp_month[uid] += 1

    markup = calendar_keyboard(year=temp_year[uid], month=temp_month[uid], day_=temp_day[uid])
    await callback.message.edit_reply_markup(markup)


async def choose_time(callback: types.CallbackQuery, callback_data: dict):
    logger.info(f"Handler called. {choose_time.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    uid = callback.from_user.id
    await delete_messages(callback.from_user.id)

    try:
        temp_records[uid].pop("number")
        temp_records[uid].pop("name")
    except Exception:
        pass

    if callback_data.get("minute") == "back":
        if "messenger" in temp_callback_data[uid]:
            return await choose_service(callback, temp_callback_data[uid].get("messenger"))

        return await choose_service(callback, temp_callback_data[uid]["service"])

    temp_callback_data[uid].update({"time": callback_data})

    minute = callback_data.get("minute") if callback_data.get("minute") == "30" else "00"
    hour = callback_data.get('hour')
    time_ = f"{hour}:{minute}"

    date_list = temp_records[uid]["date"].split(".")
    year, month, day = str(date_list[2]), str(date_list[1]), str(date_list[0])
    if (year in timeline[time_]) and (month in timeline[time_][year]) and (day in timeline[time_][year][month]):
        text = "Цей час вже занято\nОберіть час"
        return await choose_date(callback, callback_data=temp_callback_data[uid]["date"], msg_text=text)

    temp_records[uid]["time"] = time_

    msg = await callback.message.answer(text="Введите контактный номер телефона.\nПример: 0971826259",
                                        reply_markup=back_keyboard)

    msg_state_id[uid] = msg.message_id
    await ProvideContacts.Number.set()


async def write_number(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    logger.info(f"Handler called. {write_number.__name__}. user_id={message.from_user.id}")

    uid = message.from_user.id
    if isinstance(message, types.CallbackQuery):
        await message.answer()

        await state.reset_state()
        temp_records[uid].pop("time")
        return await choose_date(message, callback_data=temp_callback_data[uid]["date"])

    await Bot.get_current().delete_message(chat_id=message.chat.id, message_id=msg_state_id.get(uid))
    await message.delete()

    number = message.text
    if number.startswith('/'):
        if number == "/start":
            await state.reset_state()
            return await cmd_start(message)
        elif number == "/records":
            await state.reset_state()
            return await show_records(message)
        elif number == "/apanel":
            if uid in Config.ADMINS:
                await state.reset_state()
                return await cmd_panel(message)
        elif number == "/filling":
            await state.reset_state()
            return await start_filling(message)
        elif number == "/common_questions":
            await state.reset_state()
            return await show_questions(message)
        elif number == "/contacts":
            await state.reset_state()
            return await show_contacts(message=message)
        elif number == "/appeals":
            await state.reset_state()
            return await show_user_appeals(message=message)

    if not number.isdigit() or len(number) != 10:
        msg_wrong_number = await message.answer("Неправильный формат номера телефона\nПример: 0971826259",
                                                reply_markup=back_keyboard)
        msg_state_id[uid] = msg_wrong_number.message_id
        return

    await state.update_data(number=number)

    msg = await message.answer("Введите свое имя", reply_markup=back_keyboard)
    msg_state_id[uid] = msg.message_id

    await ProvideContacts.Name.set()


async def write_name(message: Union[types.Message, types.CallbackQuery], state: FSMContext = None):
    logger.info(f"Handler called. {write_number.__name__}. user_id={message.from_user.id}")

    uid = message.from_user.id

    if state:
        if isinstance(message, types.CallbackQuery):
            await message.answer()
            await state.reset_state()
            return await choose_time(message, callback_data=temp_callback_data[uid]["time"])

        name = str(message.text)

        await Bot.get_current().delete_message(chat_id=message.chat.id, message_id=msg_state_id.get(uid))
        await message.delete()

        if name.startswith('/'):
            if name == "/start":
                await state.reset_state()
                return await cmd_start(message)
            elif name == "/records":
                await state.reset_state()
                return await show_records(message)
            elif name == "/panel":
                if uid in Config.ADMINS:
                    await state.reset_state()
                    return await cmd_panel(message)
            elif name == "/filling":
                await state.reset_state()
                return await start_filling(message)
            elif name == "common_questions":
                await state.reset_state()
                return await show_questions(message)
            elif name == "/contacts":
                await state.reset_state()
                return await show_contacts(message=message)
            elif name == "/appeals":
                await state.reset_state()
                return await show_user_appeals(message=message)

        for i in name:
            if i.isdigit():
                msg_wrong_name = await message.answer("Имя не должно содержать цифр, попробуйте еще раз!")
                msg_state_id[uid] = msg_wrong_name.message_id
                return

        data = await state.get_data()
        number = f"+38{data.get('number')}"
        temp_records[uid]["number"] = number
        temp_records[uid]["name"] = name

        await state.reset_state()
    else:
        try:
            message = message.message
        except Exception:
            pass

    temp_records[uid].pop("further_info", None)

    text = "<b>Чтобы повысить еффективность консультацыи добавьте документы или цель обращения 👇</b>"
    try:
        msg = await message.edit_text(text=text, reply_markup=add_appeal_keyboard(add=True))
    except MessageToEditNotFound:
        msg = await message.answer(text=text, reply_markup=add_appeal_keyboard(add=True))

    add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


async def payment_record(message: Union[types.CallbackQuery, types.Message], callback_data: dict,
                         continue_: bool = False):
    logger.info(f"Handler called. {payment_record.__name__}. user_id={message.from_user.id}")

    callback = None
    uid = message.from_user.id
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        callback = message
        message = message.message

    name = callback_data.get("name")
    temp_callback_data[uid].update({"payment": callback_data})

    if name == "continue" or continue_:
        await delete_messages(uid)

        end = f"\n\n<b>К оплате {hcode(service_prices.get(temp_records[uid]['service']))} грн.</b>"
        await send_record(title="Ваша запись", end=end, record=temp_records.get(uid), uid=uid,
                          reply_markup=payment_keyboard)

        text = "<b>Чтобы оплатить консультацию, \nнажмите внизу экрана кнопку - Перейти к оплате💳</b>"
        msg = await message.answer(text=text, reply_markup=paid_keyboard)
        add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        return
    elif name == "add":
        text = "<b>Выберите файл документа 📎 и в описании к нему ✍🏼 изложите свой вопрос. Если документов нет, просто напишите вопрос.</b>"
        await message.edit_text(text=text, reply_markup=add_appeal_keyboard(add=False))

        await AddAppealToRecord.File.set()
    elif name == "back":
        return await choose_time(callback=callback, callback_data=temp_callback_data[uid]["time"])


async def add_appeal_to_record(message: Union[types.Message, types.CallbackQuery], state: FSMContext,
                               callback_data: dict = None):
    logger.info(f"Handler called {add_appeal_to_record.__name__}. user_id={message.from_user.id}")

    uid = message.from_user.id
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        await state.reset_state()

        name = callback_data.get("name")
        if name == "back":
            return await write_name(message=message)
        elif name == "continue":
            return await payment_record(message=message, callback_data=temp_callback_data[uid]["payment"],
                                        continue_=True)

    if message.content_type == types.ContentType.TEXT:
        fur_dict = {"text": message.text}
    elif message.content_type == types.ContentType.DOCUMENT:
        fur_dict = {"text": message.caption, "file_id": message.document.file_id, "file_type": "document"}
    elif message.content_type == types.ContentType.PHOTO:
        fur_dict = {"text": message.caption, "file_id": message.photo[0].file_id, "file_type": "photo"}
    elif message.content_type == types.ContentType.VIDEO:
        fur_dict = {"text": message.caption, "file_id": message.video.file_id, "file_type": "video"}
    else:
        await message.answer("<b>Вы прислали неверный тип сообщения!\bПопробуйте ещё раз</b>")
        return

    f_key = "further_info"
    if f_key in temp_records[uid]:
        temp_records[uid][f_key].append(fur_dict)
    else:
        temp_records[uid][f_key] = [fur_dict]

    await delete_messages(uid)

    msg = await message.answer(
        text="<b>Материал сохранен!\nМожете дальше присылать информацию или продолжить запись</b>",
        reply_markup=add_appeal_keyboard(add=False))
    add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


async def save_record(callback: types.CallbackQuery, callback_data: dict):
    logger.info(f"Handler called. {save_record.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    uid = callback.from_user.id
    await delete_messages(uid)

    name = callback_data.get("name")
    if name == "back":
        return await write_name(message=callback)

    # Сохраняю запись в словарь, который в on_shutdown выгружу в json
    record_id = None
    if str(uid) not in all_records:
        record_id = "1"
        all_records[str(uid)] = {record_id: temp_records[uid]}
    elif len(all_records[str(uid)]) >= Config.MAX_RECORDS_PER_USER:
        await callback.message.edit_text(
            text=f"<b>Запись не сохранена!\nУ вас уже есть активных записей: {Config.MAX_RECORDS_PER_USER}</b>")
        return
    else:
        if str(uid) in all_records and all_records[str(uid)]:
            # Отримання найбільшого ключа і додавання 1
            max_key = max(int(k) for k in all_records[str(uid)].keys())
            record_id = str(max_key + 1)
        else:
            # Якщо записів немає, починаємо з "1"
            record_id = "1"

        all_records[str(uid)].update({record_id: temp_records[uid]})
    # else:
    #     record_id = str(list(all_records[str(uid)])[-1] + 1)
    #     all_records[str(uid)].update({record_id: temp_records[uid]})

    # Занимаю временной промежуток записи в словарь, который в on_shutdown выгружу в json
    date_split = temp_records[uid]["date"].split('.')
    day, month, year = str(date_split[0]), str(date_split[1]), str(date_split[2])

    time_split = temp_records[uid]["time"].split(':')
    time_timedelta = timedelta(hours=int(time_split[0]), minutes=int(time_split[1]))
    service_duration_split = amount_time_per_service[temp_records[uid]["service"]].split(':')
    end_time = time_timedelta + timedelta(hours=int(service_duration_split[0]), minutes=int(service_duration_split[1]))

    while time_timedelta != end_time:
        time_list = str(time_timedelta).split(':')
        time_str = f"{time_list[0]}:{time_list[1]}"
        try:
            if time_timedelta > timedelta(hours=19):
                break
        except Exception:
            break

        if year in timeline[time_str]:
            if month in timeline[time_str][year]:
                timeline[time_str][year][month][day] = str(uid)
            else:
                timeline[time_str][year].update({month: {day: str(uid)}})
        else:
            timeline[time_str].update({year: {month: {day: str(uid)}}})

        time_timedelta += timedelta(hours=1)

    if str(uid) not in reminder:
        reminder[str(uid)] = {record_id: temp_records[uid].get("time")}
    else:
        reminder[str(uid)].update({record_id: temp_records[uid].get("time")})

    for adm in Config.ADMINS:
        if adm != uid:
            try:
                await send_record(title="Добавлено новую запись!", uid=str(adm), record=temp_records.get(uid),
                                  delete=False)
            except (ChatNotFound, BotBlocked):
                continue

    # await callback.message.delete()
    await send_record(title="Запись сохранена ✔", record=temp_records.get(uid), uid=str(uid),
                      reply_markup=start_keyboard(uid), delete=False)


def register_form_filling(dp: Dispatcher):
    dp.register_message_handler(start_filling, ChatTypeFilter(types.ChatType.PRIVATE),
                                Text(bot_commands.get("/filling")) | Command("filling"))
    dp.register_callback_query_handler(start_filling, ChatTypeFilter(types.ChatType.PRIVATE), text="back_price")
    dp.register_callback_query_handler(choose_service, ChatTypeFilter(types.ChatType.PRIVATE),
                                       tc.filter(title="service"))
    dp.register_callback_query_handler(choose_service, ChatTypeFilter(types.ChatType.PRIVATE),
                                       tc.filter(title="messengers"))
    dp.register_message_handler(appeal_payment, state=SendAppeal.File, content_types=types.ContentType.ANY)
    dp.register_callback_query_handler(appeal_payment, tc.filter(title="add_appeal"), state=SendAppeal.File)
    dp.register_callback_query_handler(send_appeal, tc.filter(title="service_paid"), state=SendAppeal.Payment)
    dp.register_callback_query_handler(choose_date, ChatTypeFilter(types.ChatType.PRIVATE), cc.filter(title="calendar"))
    dp.register_callback_query_handler(choose_time, ChatTypeFilter(types.ChatType.PRIVATE), tcb.filter(title="time"))

    dp.register_message_handler(write_number, state=ProvideContacts.Number)
    dp.register_callback_query_handler(write_number, state=ProvideContacts, text="back_state")
    dp.register_message_handler(write_name, state=ProvideContacts.Name)
    dp.register_callback_query_handler(write_name, state=ProvideContacts.Name, text="back_state")

    dp.register_callback_query_handler(payment_record, ChatTypeFilter(types.ChatType.PRIVATE),
                                       tc.filter(title="add_appeal"))
    dp.register_message_handler(add_appeal_to_record, state=AddAppealToRecord.File, content_types=types.ContentType.ANY)
    dp.register_callback_query_handler(add_appeal_to_record, tc.filter(title="add_appeal"),
                                       state=AddAppealToRecord.File)
    dp.register_callback_query_handler(save_record, ChatTypeFilter(types.ChatType.PRIVATE),
                                       tc.filter(title="service_paid"))
