from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import ChatTypeFilter, Command, Text

from tg_bot.keyboards.default.start_keyb import title_records
from tg_bot.keyboards.inline.remove_keyb import remove_inline
from tg_bot.misc.data_handling import all_records
from tg_bot.misc.utils import delete_messages, add_msg_to_delete, send_record


async def show_records(message: types.Message):
    uid = message.from_user.id

    await delete_messages(uid)

    if str(uid) not in all_records:
        await message.answer("<b>У вас нет активных записей 🤷🏻‍♂️</b>")
        return

    for i in all_records[str(uid)]:
        current_record = all_records[str(uid)][i]
        text = f"Запись {i}"
        markup = remove_inline(f"record_{uid}_{i}", "Удалить")
        msg = await send_record(title=text, reply_markup=markup, uid=uid, record=current_record)
        add_msg_to_delete(user_id=uid, msg_id=msg.message_id)


def register_records(dp: Dispatcher):
    dp.register_message_handler(show_records, ChatTypeFilter(types.ChatType.PRIVATE),
                                Text(title_records) | Command('records'))
