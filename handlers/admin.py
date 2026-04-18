from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
import datetime

from config import Config
from database.db import Database
from keyboards.common import admin_menu_kb
from states.booking import AdminStates
from utils.scheduler import ReminderScheduler

router = Router(name="admin_router")


def _is_admin(user_id: int, config: Config) -> bool:
    return user_id == config.admin_id


@router.message(F.text == "/admin")
async def admin_menu(message: Message, config: Config) -> None:
    if not _is_admin(message.from_user.id, config):
        await message.answer("Недостаточно прав.")
        return
    await message.answer("<b>Админ-панель</b>", parse_mode="HTML", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_add_day")
async def admin_add_day_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        return
    await state.set_state(AdminStates.add_work_day)
    await callback.message.answer("Введите дату рабочего дня в формате YYYY-MM-DD:")
    await callback.answer()


@router.message(AdminStates.add_work_day)
async def admin_add_day_finish(message: Message, db: Database, state: FSMContext) -> None:
    date = message.text.strip()
    if db.add_work_day(date):
        await message.answer("Рабочий день добавлен ✅")
    else:
        await message.answer("День уже существует.")
    await state.clear()


@router.callback_query(F.data == "admin_add_slot")
async def admin_add_slot_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        return
    await state.set_state(AdminStates.add_slot_date)
    await callback.message.answer("Введите дату для слота (YYYY-MM-DD):")
    await callback.answer()


@router.message(AdminStates.add_slot_date)
async def admin_add_slot_date(message: Message, state: FSMContext, db: Database) -> None:
    date = message.text.strip()
    if not db.day_exists_and_open(date):
        await message.answer("Сначала добавьте рабочий день или откройте его.")
        await state.clear()
        return
    await state.update_data(date=date)
    await state.set_state(AdminStates.add_slot_time)
    await message.answer("Введите время слота (HH:MM):")


@router.message(AdminStates.add_slot_time)
async def admin_add_slot_time(message: Message, state: FSMContext, db: Database) -> None:
    time = message.text.strip()
    data = await state.get_data()
    if db.add_time_slot(data["date"], time):
        await message.answer("Слот добавлен ✅")
    else:
        await message.answer("Такой слот уже существует.")
    await state.clear()


@router.callback_query(F.data == "admin_del_slot")
async def admin_del_slot_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        return
    await state.set_state(AdminStates.del_slot_date)
    await callback.message.answer("Введите дату слота для удаления (YYYY-MM-DD):")
    await callback.answer()


@router.message(AdminStates.del_slot_date)
async def admin_del_slot_date(message: Message, state: FSMContext) -> None:
    await state.update_data(date=message.text.strip())
    await state.set_state(AdminStates.del_slot_time)
    await message.answer("Введите время слота для удаления (HH:MM):")


@router.message(AdminStates.del_slot_time)
async def admin_del_slot_time(message: Message, state: FSMContext, db: Database) -> None:
    time = message.text.strip()
    data = await state.get_data()
    if db.delete_time_slot(data["date"], time):
        await message.answer("Слот удален ✅")
    else:
        await message.answer("Слот не найден.")
    await state.clear()


@router.callback_query(F.data == "admin_close_day")
async def admin_close_day_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        return
    await state.set_state(AdminStates.close_day)
    await callback.message.answer("Введите дату для закрытия (YYYY-MM-DD):")
    await callback.answer()


@router.message(AdminStates.close_day)
async def admin_close_day_finish(message: Message, state: FSMContext, db: Database) -> None:
    date = message.text.strip()
    if db.close_day(date):
        await message.answer("День закрыт ✅")
    else:
        await message.answer("День не найден.")
    await state.clear()


@router.callback_query(F.data == "admin_open_day")
async def admin_open_day_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        return
    await state.set_state(AdminStates.open_day)
    await callback.message.answer("Введите дату для открытия (YYYY-MM-DD):")
    await callback.answer()


@router.message(AdminStates.open_day)
async def admin_open_day_finish(message: Message, state: FSMContext, db: Database) -> None:
    date = message.text.strip()
    if db.open_day(date):
        await message.answer("День открыт ✅")
    else:
        await message.answer("День не найден.")
    await state.clear()


@router.callback_query(F.data == "admin_schedule")
async def admin_schedule_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        return
    await state.set_state(AdminStates.schedule_date)
    await callback.message.answer("Введите дату для просмотра расписания (YYYY-MM-DD):")
    await callback.answer()


@router.message(AdminStates.schedule_date)
async def admin_schedule_show(message: Message, state: FSMContext, db: Database) -> None:
    date = message.text.strip()
    schedule = db.get_schedule_for_date(date)
    if not schedule:
        await message.answer("На эту дату слотов нет.")
        await state.clear()
        return

    lines = [f"<b>Расписание на {date}</b>"]
    for item in schedule:
        if item["booking_id"]:
            lines.append(
                f"{item['time']} — ❌ занято ({item['full_name']}, {item['phone']}, id={item['booking_id']})"
            )
        else:
            lines.append(f"{item['time']} — ✅ свободно")

    await message.answer("\n".join(lines), parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "admin_cancel_booking")
async def admin_cancel_booking_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        return
    await state.set_state(AdminStates.cancel_booking_id)
    await callback.message.answer(
        "Введите ID записи для отмены.\n"
        "ID можно увидеть в пункте 'Расписание на дату'."
    )
    await callback.answer()


@router.message(AdminStates.cancel_booking_id)
async def admin_cancel_booking_finish(
    message: Message,
    state: FSMContext,
    db: Database,
    scheduler: ReminderScheduler,
) -> None:
    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("ID должен быть числом.")
        return
    booking = db.cancel_booking_by_id(int(raw))
    if not booking:
        await message.answer("Запись не найдена.")
        await state.clear()
        return
    scheduler.remove_reminder(booking["reminder_job_id"])
    await message.answer("Запись клиента отменена ✅")
    await state.clear()


@router.callback_query(F.data == "admin_generate_schedule")
async def admin_generate_schedule(callback: CallbackQuery, config: Config, db: Database) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await callback.message.answer("Генерирую расписание на год вперед...")
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=365)
    current_date = today
    added_days = 0
    added_slots = 0
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Понедельник-пятница
            if db.add_work_day(current_date.isoformat()):
                added_days += 1
                # Добавить слоты с 9:00 до 18:00 с шагом 1 час
                for hour in range(9, 18):
                    time_str = f"{hour:02d}:00"
                    if db.add_time_slot(current_date.isoformat(), time_str):
                        added_slots += 1
        current_date += datetime.timedelta(days=1)
    await callback.message.answer(f"Расписание сгенерировано: {added_days} дней, {added_slots} слотов.")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_"))
async def reject_non_admin(callback: CallbackQuery, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer("Недостаточно прав", show_alert=True)
