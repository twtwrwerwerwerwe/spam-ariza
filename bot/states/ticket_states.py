from aiogram.fsm.state import State, StatesGroup


class TicketForm(StatesGroup):
    full_name = State()
    phone = State()
    category = State()


class BroadcastForm(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()


class AddAdminForm(StatesGroup):
    waiting_for_id = State()


class RemoveAdminForm(StatesGroup):
    waiting_for_id = State()
