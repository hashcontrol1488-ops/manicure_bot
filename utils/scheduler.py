from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.db import Database


class ReminderScheduler:
    def __init__(self, scheduler: AsyncIOScheduler, db: Database) -> None:
        self.scheduler = scheduler
        self.db = db

    async def send_reminder(self, bot: Bot, user_id: int, booking_time: str) -> None:
        text = (
            f"Напоминаем, что вы записаны на наращивание ресниц завтра в <b>{booking_time}</b>.\n"
            "Ждём вас ❤️"
        )
        await bot.send_message(user_id, text, parse_mode="HTML")

    def schedule_reminder(
        self,
        bot: Bot,
        booking_id: int,
        user_id: int,
        date_str: str,
        time_str: str,
    ) -> str | None:
        visit_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        remind_dt = visit_dt - timedelta(hours=24)
        if remind_dt <= datetime.now():
            return None

        job_id = f"reminder_{booking_id}"
        self.scheduler.add_job(
            self.send_reminder,
            "date",
            run_date=remind_dt,
            id=job_id,
            replace_existing=True,
            kwargs={"bot": bot, "user_id": user_id, "booking_time": time_str},
        )
        return job_id

    def remove_reminder(self, job_id: str | None) -> None:
        if not job_id:
            return
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.remove_job(job_id)

    def restore_jobs(self, bot: Bot) -> None:
        bookings = self.db.get_bookings_for_restore()
        for booking in bookings:
            visit_dt = datetime.strptime(
                f"{booking['date']} {booking['time']}",
                "%Y-%m-%d %H:%M",
            )
            remind_dt = visit_dt - timedelta(hours=24)
            if remind_dt <= datetime.now():
                continue

            job_id = f"reminder_{booking['id']}"
            self.scheduler.add_job(
                self.send_reminder,
                "date",
                run_date=remind_dt,
                id=job_id,
                replace_existing=True,
                kwargs={
                    "bot": bot,
                    "user_id": booking["user_id"],
                    "booking_time": booking["time"],
                },
            )
            self.db.update_reminder_job_id(booking["id"], job_id)
