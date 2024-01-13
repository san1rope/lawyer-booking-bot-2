from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import ChatTypeFilter, Command, Text
from aiogram.utils.markdown import hcode

from tg_bot.filters.isAdmin import IsAdmin
from tg_bot.keyboards.inline.admin_keyb import panel_inline
from tg_bot.misc.data_handling import all_records, appeals
from tg_bot.misc.utils import delete_messages, add_msg_to_delete


async def cmd_panel(message: types.Message | types.CallbackQuery):
    if isinstance(message, types.CallbackQuery):
        uid = message.from_user.id
        message = message.message
    else:
        uid = message.from_user.id
        await message.delete()

    await delete_messages(uid)

    records_count = 0
    for user_id in all_records:
        for record_index in all_records[user_id]:
            if all_records[user_id][record_index].get("service") == "Вихідний":
                continue

            records_count += 1

    appeals_count = 0
    for appeal in appeals:
        if appeal == "last_id":
            continue

        appeals_count += len(appeals.get(appeal))

    text = [
        "<b>Вы вошли в админ панель</b>",
        f"<b>Активных записей: {hcode(str(records_count))}</b>",
        f"<b>Активных обращений: {hcode(str(appeals_count))}</b>",
        "\n<b>Выберите одну из функций</b>"
    ]
    msg = await message.answer('\n\n'.join(text), reply_markup=panel_inline)
    add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


def register_panel(dp: Dispatcher):
    dp.register_message_handler(cmd_panel, ChatTypeFilter(types.ChatType.PRIVATE), IsAdmin(),
                                Text("Меню администратора") | Command('apanel'))
