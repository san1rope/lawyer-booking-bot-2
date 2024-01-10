import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import ChatTypeFilter, Text, Command
from aiogram.utils.exceptions import BadRequest
from aiogram.utils.markdown import hcode

from tg_bot.keyboards.inline.callback_data import temp_callback as tc
from tg_bot.keyboards.inline.remove_confirm_keyb import remove_confirm
from tg_bot.keyboards.inline.remove_keyb import remove_inline
from tg_bot.misc.data_handling import appeals
from tg_bot.misc.utils import delete_messages, add_msg_to_delete

logger = logging.getLogger(__name__)


async def show_user_appeals(message: types.Message):
    logger.info(f"Handler called. {show_user_appeals.__name__}. user_id={message.from_user.id}")

    await delete_messages(user_id=message.from_user.id)

    user_appeals = appeals.get(str(message.from_user.id))
    if not user_appeals:
        return await message.answer("<b>У вас нет активных обращений!</b>")

    for appeal in user_appeals:
        text = [
            f"<b>Обращение №{appeal.get('id')}</b>",
            f"<b>ID пользователя: {hcode(str(message.from_user.id))}</b>",
            f"<b>Полное имя: {hcode(appeal.get('full_name'))}</b>",
        ]

        appeal_username = appeal.get("username")
        if appeal_username:
            text.append(f"<b>Username пользователя: {hcode(appeal_username)}</b>")

        file_id = appeal.get("file_id")
        markup = remove_inline(title="Удалить", title_arg="remove_appeal_user", name=str(appeal.get('id')))

        msg = None
        appeal_text = appeal.get('text')
        if appeal_text:
            text.append(f"\n{appeal_text}")

        if file_id:
            file_type = appeal.get("file_type")
            if file_type == "photo":
                msg = await message.answer_photo(photo=file_id, caption='\n'.join(text), reply_markup=markup)
            elif file_type == "video":
                msg = await message.answer_video(video=file_id, caption='\n'.join(text), reply_markup=markup)
            elif file_type == "document":
                msg = await message.answer_document(document=file_id, caption='\n'.join(text), reply_markup=markup)
        else:
            msg = await message.answer(text='\n'.join(text), reply_markup=markup)

        add_msg_to_delete(user_id=message.from_user.id, msg_id=msg.message_id)


async def remove_confirm_appeal_user(callback: types.CallbackQuery, callback_data: dict):
    logger.info(f"Handler called. {remove_confirm_appeal_user.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    removal_appeal_id = callback_data.get("name")
    user_appeals = appeals.get(str(callback.from_user.id))

    text_error_remove = f"Обращение №{removal_appeal_id} было удалено адинистратором либо на него ответили!"
    if not user_appeals:
        try:
            return await callback.message.edit_caption(caption=text_error_remove, reply_markup=None)
        except BadRequest:
            return await callback.message.edit_text(text=text_error_remove, reply_markup=None)

    index = None
    for appeal, counter in zip(user_appeals, range(len(user_appeals))):
        if str(appeal.get("id")) == str(removal_appeal_id):
            index = counter
            break

    if index is None:
        try:
            return await callback.message.edit_caption(caption=text_error_remove, reply_markup=None)
        except BadRequest:
            return await callback.message.edit_text(text=text_error_remove, reply_markup=None)

    text = f"<b>Вы уверены в удалении вашего обращения №{removal_appeal_id}?</b>"
    markup = remove_confirm(name=str(removal_appeal_id), title_arg="agreement_appeal_user")
    try:
        await callback.message.edit_caption(caption=text, reply_markup=remove_confirm(name=str(removal_appeal_id),
                                                                                      title_arg="agreement_appeal_user")
                                            )
    except BadRequest:
        await callback.message.edit_text(text=text, reply_markup=markup)


async def remove_appeal_user(callback: types.CallbackQuery, callback_data: dict):
    logger.info(f"Handler called. {remove_appeal_user.__name__}. user_id={callback.from_user.id}")
    await callback.answer()

    agreement = callback_data.get("name")
    if agreement == "disagree":
        text = f"<b>Вы отменили удаление обращения!</b>"
        try:
            return await callback.message.edit_caption(caption=text, reply_markup=None)
        except BadRequest:
            return await callback.message.edit_text(text=text, reply_markup=None)

    appeal_id = agreement
    user_appeals = appeals.get(str(callback.from_user.id))
    text_error_remove = f"Обращение №{appeal_id} было удалено адинистратором либо на него ответили!"
    if not user_appeals:
        try:
            return await callback.message.edit_caption(caption=text_error_remove, reply_markup=None)
        except BadRequest:
            return await callback.message.edit_text(text=text_error_remove, reply_markup=None)

    index = None
    for appeal, counter in zip(user_appeals, range(len(user_appeals))):
        if str(appeal.get("id")) == str(appeal_id):
            index = counter
            break

    if index is None:
        try:
            return await callback.message.edit_caption(caption=text_error_remove, reply_markup=None)
        except BadRequest:
            return await callback.message.edit_text(text=text_error_remove, reply_markup=None)

    appeals[str(callback.from_user.id)].pop(index)
    if not len(appeals[str(callback.from_user.id)]):
        appeals.pop(str(callback.from_user.id))

    text = f"<b>Вы удалили свое обращение №{appeal_id}!</b>"
    try:
        await callback.message.edit_caption(caption=text, reply_markup=None)
    except BadRequest:
        await callback.message.edit_text(text=text, reply_markup=None)


def register_appeals(dp: Dispatcher):
    dp.register_message_handler(show_user_appeals, ChatTypeFilter(types.ChatType.PRIVATE),
                                Text("Обращения") | Command("appeals"))
    dp.register_callback_query_handler(remove_confirm_appeal_user, ChatTypeFilter(types.ChatType.PRIVATE),
                                       tc.filter(title="remove_appeal_user"))
    dp.register_callback_query_handler(remove_appeal_user, ChatTypeFilter(types.ChatType.PRIVATE),
                                       tc.filter(title="agreement_appeal_user"))
