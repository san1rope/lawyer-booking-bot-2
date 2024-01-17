from aiogram.dispatcher.filters.state import StatesGroup, State


class ProvideContacts(StatesGroup):
    Number = State()
    Name = State()


class SendAppeal(StatesGroup):
    File = State()
    Payment = State()


class AnswerAppeal(StatesGroup):
    Answer = State()
    Confirm = State()


class FindData(StatesGroup):
    UserId = State()


class AddAppealToRecord(StatesGroup):
    File = State()
