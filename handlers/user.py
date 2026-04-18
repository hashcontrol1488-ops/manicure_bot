from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import Config
from database.db import Database
from keyboards.calendar import confirm_kb, dates_kb, slots_kb
from keyboards.common import main_menu_kb, portfolio_kb, subscription_kb
from states.booking import BookingStates
from utils.scheduler import ReminderScheduler

router = Router(name="user_router")


async def _is_subscribed(bot: Bot, user_id: int, channel_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
    except TelegramBadRequest:
        return False
    return member.status in {"member", "administrator", "creator"}


async def _require_subscription(
    callback: CallbackQuery,
    bot: Bot,
    config: Config,
) -> bool:
    if callback.from_user.id == config.admin_id:
        return True  # Администратор не нуждается в подписке
    if not config.channel_id or not config.channel_link:
        return True
    if await _is_subscribed(bot, callback.from_user.id, config.channel_id):
        return True
    await callback.message.answer(
        "Для записи необходимо подписаться на канал",
        reply_markup=subscription_kb(config.channel_link),
    )
    return False


@router.message(F.text == "/start")
async def start_handler(message: Message) -> None:
    text = (
        "💅 <b>Добро пожаловать в Nails Master!</b>\n\n"
        "Здесь вы можете:\n"
        "• записаться на маникюр\n"
        "• посмотреть свои записи\n"
        "• изучить прайс и портфолио\n\n"
        "Выберите нужный раздел ниже 👇"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Главное меню 👇", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "prices")
async def prices_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "💲 <b>Прайс:</b>\n\n"
        "— Маникюр: <b>1500₽</b>\n"
        "— Гель-лак: <b>2000₽</b>\n"
        "— Дизайн: <b>от 300₽</b>",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "portfolio")
async def portfolio_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "📸 Наши работы — вдохновляйтесь ✨\n\n"
        "— Нюд дизайн\n"
        "— Френч\n"
        "— Яркий дизайн",
        reply_markup=portfolio_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def contacts_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "📍 Мы находимся:\n"
        "(адрес)\n\n"
        "📞 Телефон:\n"
        "(номер)",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, bot: Bot, config: Config) -> None:
    if not config.channel_id or not config.channel_link:
        await callback.message.answer("Проверка подписки сейчас отключена администратором.")
        await callback.answer()
        return
    if await _is_subscribed(bot, callback.from_user.id, config.channel_id):
        await callback.message.answer("Подписка подтверждена ✅ Теперь запись доступна.")
    else:
        await callback.message.answer(
            "Подписка пока не найдена.\nПодпишитесь и нажмите кнопку снова ✨",
            reply_markup=subscription_kb(config.channel_link),
        )
    await callback.answer()


@router.callback_query(F.data == "start_booking")
async def booking_start(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    bot: Bot,
    config: Config,
) -> None:
    if not await _require_subscription(callback, bot, config):
        await callback.answer()
        return

    if db.user_has_booking(callback.from_user.id):
        await callback.message.answer(
            "У вас уже есть активная запись.\nСначала отмените текущую ❌",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
        return

    dates = db.get_available_dates(days_ahead=30)
    if not dates:
        await callback.message.answer(
            "Свободных дат на ближайший месяц пока нет.\n"
            "Напишите нам позже — обязательно подберем удобное окно ✨",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
        return

    await state.set_state(BookingStates.choosing_date)
    await callback.message.answer(
        "💅 Отлично! Давайте подберем удобное время.\n\n"
        "Выберите услугу 👇\n"
        "Маникюр",
    )
    await callback.message.answer(
        "Выберите дату 📅",
        parse_mode="HTML",
        reply_markup=dates_kb(dates),
    )
    await callback.answer()


@router.callback_query(F.data == "choose_date")
async def choose_date_again(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    dates = db.get_available_dates(days_ahead=30)
    if not dates:
        await callback.message.answer("Свободных дат на ближайший месяц пока нет.")
        await callback.answer()
        return
    await state.set_state(BookingStates.choosing_date)
    await callback.message.answer("Выберите дату 📅", reply_markup=dates_kb(dates))
    await callback.answer()


@router.callback_query(BookingStates.choosing_date, F.data.startswith("date:"))
async def booking_pick_date(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    selected_date = callback.data.split(":", maxsplit=1)[1]
    slots = db.get_available_slots(selected_date)
    if not slots:
        await callback.message.answer(
            "На выбранную дату нет свободного времени.\n"
            "Выберите другую дату 📅"
        )
        await callback.answer()
        return
    await state.update_data(date=selected_date)
    await state.set_state(BookingStates.choosing_time)
    await callback.message.answer(
        "Выберите удобное время ⏰",
        parse_mode="HTML",
        reply_markup=slots_kb(selected_date, slots),
    )
    await callback.answer()


@router.callback_query(BookingStates.choosing_time, F.data.startswith("time:"))
async def booking_pick_time(callback: CallbackQuery, state: FSMContext) -> None:
    logging.info(f"Callback data: {callback.data}")
    try:
        _, date, time = callback.data.split(":", 2)
        logging.info("Parsed date and time")
        await state.update_data(date=date, time=time)
        logging.info("Updated state data")
        await state.set_state(BookingStates.entering_name)
        logging.info("Set state to entering_name")
        await callback.message.answer("Введите ваше имя 👇")
        logging.info("Sent message")
        await callback.answer()
        logging.info("Time selection handled successfully")
    except Exception as e:
        logging.error(f"Error in booking_pick_time: {e}")
        await callback.answer()


@router.message(BookingStates.entering_name)
async def booking_get_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text.strip())
    await state.set_state(BookingStates.entering_phone)
    await message.answer("Введите номер телефона 📞")


@router.message(BookingStates.entering_phone)
async def booking_get_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    data = await state.get_data()
    await state.update_data(phone=phone)
    await state.set_state(BookingStates.confirming)
    await message.answer(
        "<b>Подтвердите запись:</b>\n\n"
        f"📍 Дата: <b>{data['date']}</b>\n"
        f"⏰ Время: <b>{data['time']}</b>\n"
        f"👤 Имя: <b>{data['full_name']}</b>\n"
        f"📞 Телефон: <b>{phone}</b>",
        parse_mode="HTML",
        reply_markup=confirm_kb(),
    )


@router.callback_query(BookingStates.confirming, F.data == "confirm_booking")
async def booking_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    config: Config,
    scheduler: ReminderScheduler,
    bot: Bot,
) -> None:
    data = await state.get_data()
    user_id = callback.from_user.id
    if db.user_has_booking(user_id):
        await callback.message.answer("У вас уже есть активная запись.")
        await state.clear()
        await callback.answer()
        return

    created = db.create_booking(
        user_id=user_id,
        username=callback.from_user.username,
        full_name=data["full_name"],
        phone=data["phone"],
        date=data["date"],
        time=data["time"],
    )
    if not created:
        await callback.message.answer(
            "Этот слот уже занят.\n"
            "Пожалуйста, выберите другую дату или время ✨",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        await callback.answer()
        return

    booking = db.get_user_booking(user_id)
    if booking:
        job_id = scheduler.schedule_reminder(
            bot=bot,
            booking_id=booking["id"],
            user_id=user_id,
            date_str=booking["date"],
            time_str=booking["time"],
        )
        db.update_reminder_job_id(booking["id"], job_id)

    text_for_admin = (
        "<b>Новая запись</b>\n"
        f"ID пользователя: <code>{user_id}</code>\n"
        f"Username: @{callback.from_user.username or 'нет'}\n"
        f"Имя: <b>{data['full_name']}</b>\n"
        f"Телефон: <b>{data['phone']}</b>\n"
        f"Дата: <b>{data['date']}</b>\n"
        f"Время: <b>{data['time']}</b>"
    )
    await bot.send_message(config.admin_id, text_for_admin, parse_mode="HTML")

    channel_text = (
        "<b>Обновление расписания</b>\n"
        f"✅ Новая запись на <b>{data['date']} {data['time']}</b>\n"
        f"Клиент: <b>{data['full_name']}</b>"
    )
    if config.channel_id:
        await bot.send_message(config.channel_id, channel_text, parse_mode="HTML")

    await callback.message.answer(
        "🎉 Вы записаны! Ждем вас 💅",
        reply_markup=main_menu_kb(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery, db: Database) -> None:
    booking = db.get_user_booking(callback.from_user.id)
    if not booking:
        await callback.message.answer(
            "У вас пока нет активных записей",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
        return
    await callback.message.answer(
        "📅 <b>Ваша запись:</b>\n\n"
        f"💅 Услуга: <b>Маникюр</b>\n"
        f"📍 Дата: <b>{booking['date']}</b>\n"
        f"⏰ Время: <b>{booking['time']}</b>",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_my_booking")
async def cancel_booking_confirm_prompt(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "👉 Вы уверены, что хотите отменить запись?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Да, отменить", callback_data="confirm_cancel_booking")],
                [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_cancel_booking")
async def cancel_my_booking(
    callback: CallbackQuery,
    db: Database,
    config: Config,
    scheduler: ReminderScheduler,
    bot: Bot,
) -> None:
    booking = db.cancel_booking_by_user(callback.from_user.id)
    if not booking:
        await callback.message.answer(
            "У вас нет записи для отмены.",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
        return

    scheduler.remove_reminder(booking["reminder_job_id"])
    await callback.message.answer("Запись успешно отменена ❌", reply_markup=main_menu_kb())
    await bot.send_message(
        config.admin_id,
        (
            "<b>Отмена записи клиентом</b>\n"
            f"Пользователь: <code>{callback.from_user.id}</code>\n"
            f"Дата: <b>{booking['date']}</b>\n"
            f"Время: <b>{booking['time']}</b>"
        ),
        parse_mode="HTML",
    )
    if config.channel_id:
        await bot.send_message(
            config.channel_id,
            (
                "<b>Обновление расписания</b>\n"
                f"❌ Запись отменена: <b>{booking['date']} {booking['time']}</b>\n"
                "Слот снова свободен."
            ),
            parse_mode="HTML",
        )
    await callback.answer()
