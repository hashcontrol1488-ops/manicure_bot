import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import load_config
from database.db import Database
from handlers import admin, user
from utils.scheduler import ReminderScheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    db = Database(config.db_path)
    scheduler_engine = AsyncIOScheduler()
    reminder_scheduler = ReminderScheduler(scheduler_engine, db)

    scheduler_engine.start()
    reminder_scheduler.restore_jobs(bot)

    # Передаем зависимости в обработчики через middleware data.
    dp["config"] = config
    dp["db"] = db
    dp["scheduler"] = reminder_scheduler

    dp.include_router(user.router)
    dp.include_router(admin.router)

    try:
        # Ensure long polling is not blocked by an old webhook configuration.
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler_engine.shutdown(wait=False)
        db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
