from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()


class AdminStates(StatesGroup):
    add_work_day = State()
    add_slot_date = State()
    add_slot_time = State()
    del_slot_date = State()
    del_slot_time = State()
    close_day = State()
    open_day = State()
    schedule_date = State()
    cancel_booking_id = State()
