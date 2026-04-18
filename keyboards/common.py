from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💅 Записаться", callback_data="start_booking")],
            [InlineKeyboardButton(text="📅 Моя запись", callback_data="my_booking")],
            [InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_my_booking")],
            [InlineKeyboardButton(text="💲 Прайс", callback_data="prices")],
            [InlineKeyboardButton(text="📸 Портфолио", callback_data="portfolio")],
            [InlineKeyboardButton(text="📍 Контакты", callback_data="contacts")],
        ]
    )


def portfolio_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Смотреть портфолио",
                    url="https://ru.pinterest.com/crystalwithluv/_created/",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")],
        ]
    )


def subscription_kb(channel_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Подписаться", url=channel_link)],
            [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")],
        ]
    )


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить рабочий день", callback_data="admin_add_day")],
            [InlineKeyboardButton(text="Добавить слот", callback_data="admin_add_slot")],
            [InlineKeyboardButton(text="Удалить слот", callback_data="admin_del_slot")],
            [InlineKeyboardButton(text="Закрыть день", callback_data="admin_close_day")],
            [InlineKeyboardButton(text="Открыть день", callback_data="admin_open_day")],
            [InlineKeyboardButton(text="Расписание на дату", callback_data="admin_schedule")],
            [InlineKeyboardButton(text="Отменить запись клиента", callback_data="admin_cancel_booking")],
        ]
    )
