import logging
from typing import Union, List

from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.utils.markdown import hcode

from tg_bot.handlers.admin.panel import cmd_panel
from tg_bot.keyboards.inline.admin_keyb import appeals_inline, panel_inline
from tg_bot.keyboards.inline.callback_data import temp_callback as tc
from tg_bot.keyboards.inline.remove_confirm_keyb import remove_confirm
from tg_bot.misc.data_handling import appeals
from tg_bot.misc.states import AnswerAppeal
from tg_bot.misc.utils import delete_messages, add_msg_to_delete

logger = logging.getLogger(__name__)
temp_appeals = {}


async def show_appeals(callback: types.CallbackQuery):
    logger.info(f"Handler called. {show_appeals.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    await delete_messages(callback.from_user.id)

    try:
        current_uid = list(appeals.keys())[1]
    except Exception:
        await delete_messages(callback.from_user.id)
        msg = await callback.message.answer("<b>На данный момент активных обращений нет!</b>",
                                            reply_markup=panel_inline)
        add_msg_to_delete(user_id=callback.from_user.id, msg_id=msg.message_id)
        return

    current_appeal = appeals[current_uid][0]
    markup = appeals_inline(delete=True)
    text = [
        f"<b>Обращение №{current_appeal.get('id')}</b>",
        f"<b>ID пользователя: {hcode(str(current_uid))}</b>",
        f"<b>Полное имя: {hcode(current_appeal.get('full_name'))}</b>",
    ]

    appeal_username = current_appeal.get("username")
    if appeal_username:
        text.append(f"<b>Username пользователя: {hcode(appeal_username)}</b>\n")

    appeal_file_id = current_appeal.get("file_id")
    if appeal_file_id:
        appeal_text = current_appeal.get("text")
        if appeal_text:
            text.append(appeal_text)

        text.append("\n<b>Пришлите ответ на обращение одним сообщением!</b>")
        appeal_file_type = current_appeal.get("file_type")
        if appeal_file_type == "photo":
            msg = await callback.message.answer_photo(photo=appeal_file_id, caption='\n'.join(text),
                                                      reply_markup=markup)
        elif appeal_file_type == "video":
            msg = await callback.message.answer_video(video=appeal_file_id, caption='\n'.join(text),
                                                      reply_markup=markup)
        elif appeal_file_type == "document":
            msg = await callback.message.answer_document(document=appeal_file_id, caption='\n'.join(text),
                                                         reply_markup=markup)
        else:
            await callback.message.answer(text="<b>Неверный тип сообщения!\nПопробуйте ещё раз.</b>")
            return
    else:
        msg = await callback.message.answer(text='\n'.join(text), reply_markup=markup)

    temp_appeals[callback.from_user.id] = {"user_id": current_uid, "appeal_id": str(current_appeal.get('id'))}
    add_msg_to_delete(user_id=callback.from_user.id, msg_id=msg.message_id)
    await AnswerAppeal.Answer.set()


async def back_to_panel(callback: types.CallbackQuery):
    logger.info(f"Handler called. {back_to_panel.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    return await cmd_panel(callback.message)


async def appeal_answer(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    logger.info(f"Handler called. {appeal_answer.__name__}. user_id={message.from_user.id}")

    temp_appeal = temp_appeals.get(message.from_user.id)
    appeal_user_id = temp_appeal.get("user_id")
    appeal_id = temp_appeal.get("appeal_id")

    if isinstance(message, types.CallbackQuery):
        if message.data == "back_from_appeal":
            await state.reset_state()
            return await back_to_panel(message)
        elif message.data == "delete_appeal":
            await delete_messages(user_id=message.from_user.id)
            msg = await message.message.answer(text=f"<b>Вы точно хотите удалить обращение №{appeal_id}?</b>",
                                               reply_markup=remove_confirm("temp"))
            add_msg_to_delete(user_id=message.from_user.id, msg_id=msg.message_id)
            await AnswerAppeal.Confirm.set()
            return

    text = [f"<b>Администратор ответил на ваше обращение №{appeal_id}:</b>\n"]
    if message.content_type == types.ContentType.TEXT:
        if message.text:
            text.append(message.text)

        await Bot.get_current().send_message(chat_id=int(appeal_user_id), text='\n'.join(text))
    elif message.content_type == types.ContentType.DOCUMENT:
        if message.caption:
            text.append(message.caption)

        await Bot.get_current().send_document(chat_id=int(appeal_user_id), document=message.document.file_id,
                                              caption='\n'.join(text))
    elif message.content_type == types.ContentType.PHOTO:
        print("photo")
        if message.caption:
            text.append(message.caption)

        await Bot.get_current().send_photo(chat_id=int(appeal_user_id), photo=message.photo[-1].file_id,
                                           caption='\n'.join(text))
    elif message.content_type == types.ContentType.VIDEO:
        if message.caption:
            text.append(message.caption)

        await Bot.get_current().send_video(chat_id=int(appeal_user_id), video=message.video.file_id,
                                           caption='\n'.join(text))
    else:
        await message.answer("<b>Вы прислали неверный тип сообщения!\bПопробуйте ещё раз</b>")
        return

    await delete_messages(user_id=message.from_user.id)

    user_appeals = appeals.get(str(appeal_user_id))
    text_error_answer = f"<b>Обращение было удалено либо на него дал ответ другой администратор!</b>"
    if not user_appeals:
        await state.reset_state()
        return await message.answer(text=text_error_answer, reply_markup=appeals_inline(continue_=True))
    else:
        flag = False
        for appeal in user_appeals:
            if str(appeal["id"]) == str(appeal_id):
                flag = False
                break

            flag = True

        if flag:
            await state.reset_state()
            return await message.answer(text=text_error_answer, reply_markup=appeals_inline(continue_=True))

    appeals[str(appeal_user_id)].pop(0)
    if len(appeals[str(appeal_user_id)]) == 0:
        appeals.pop(str(appeal_user_id))

    msg = await message.answer(f"<b>Вы отправили ответ на обращение №{appeal_id}!</b>",
                               reply_markup=appeals_inline(continue_=True))
    add_msg_to_delete(user_id=message.from_user.id, msg_id=msg.message_id)
    await state.reset_state()


async def remove_appeal(callback: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logger.info(f"Handler called. {remove_appeal.__name__}. user_id={callback.from_user.id}")

    await delete_messages(callback.from_user.id)

    agreement = callback_data.get("name")
    if agreement == "disagree":
        await state.reset_state()
        return await show_appeals(callback)
    else:
        current_appeal = temp_appeals.get(callback.from_user.id)
        appeal_user_id = current_appeal.get("user_id")
        appeal_id = current_appeal.get("appeal_id")

        flag = False
        user_appeals: List[dict] = appeals.get(str(appeal_user_id))
        if not user_appeals:
            print(2222222)
            flag = True

        if not flag:
            print(f"user_appeals = {user_appeals}")
            for appeal, counter in zip(user_appeals, range(len(user_appeals))):
                print(f"id = {appeal.get('id')}")
                if str(appeal.get("id")) == str(appeal_id):
                    appeals[str(appeal_user_id)].pop(counter)
                    if not len(appeals[str(appeal_user_id)]):
                        appeals.pop(str(appeal_user_id))

                    flag = False
                    break

                flag = True

        if flag:
            msg = await callback.message.answer(
                text=f"<b>Обращение №{appeal_id} было удалено!</b>",
                reply_markup=appeals_inline(continue_=True))
            add_msg_to_delete(user_id=callback.from_user.id, msg_id=msg.message_id)
        else:
            msg = await callback.message.answer(text=f"<b>Вы успешно удалили обращение №{appeal_id}!</b>",
                                                reply_markup=appeals_inline(continue_=True))
            add_msg_to_delete(user_id=callback.from_user.id, msg_id=msg.message_id)

    await state.reset_state()


def register_admin_appeals(dp: Dispatcher):
    dp.register_callback_query_handler(show_appeals, ChatTypeFilter(types.ChatType.PRIVATE), text="appeals")
    dp.register_callback_query_handler(show_appeals, ChatTypeFilter(types.ChatType.PRIVATE), text="continue_appeals")
    dp.register_message_handler(appeal_answer, state=AnswerAppeal.Answer, content_types=types.ContentType.ANY)
    dp.register_callback_query_handler(appeal_answer, state=AnswerAppeal.Answer)
    dp.register_callback_query_handler(back_to_panel, ChatTypeFilter(types.ChatType.PRIVATE), text="back_from_appeal")
    dp.register_callback_query_handler(remove_appeal, tc.filter(title="agreement"), state=AnswerAppeal.Confirm)
