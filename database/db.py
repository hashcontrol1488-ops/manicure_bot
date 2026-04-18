import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Any


class Database:
    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        # Log database status
        cursor = self.conn.cursor()
        work_days_count = cursor.execute("SELECT COUNT(*) FROM work_days").fetchone()[0]
        time_slots_count = cursor.execute("SELECT COUNT(*) FROM time_slots").fetchone()[0]
        bookings_count = cursor.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        logging.info(f"Database initialized: {work_days_count} work_days, {time_slots_count} time_slots, {bookings_count} bookings")

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS work_days (
                date TEXT PRIMARY KEY,
                is_closed INTEGER DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                UNIQUE(date, time)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                reminder_job_id TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(date, time)
            )
            """
        )
        self.conn.commit()

    def add_work_day(self, date: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO work_days(date, is_closed) VALUES (?, 0)",
            (date,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def close_day(self, date: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE work_days SET is_closed = 1 WHERE date = ?", (date,))
        self.conn.commit()
        return cursor.rowcount > 0

    def open_day(self, date: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE work_days SET is_closed = 0 WHERE date = ?", (date,))
        self.conn.commit()
        return cursor.rowcount > 0

    def day_exists_and_open(self, date: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM work_days WHERE date = ? AND is_closed = 0",
            (date,),
        )
        return cursor.fetchone() is not None

    def add_time_slot(self, date: str, time: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO time_slots(date, time) VALUES (?, ?)",
            (date, time),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_time_slot(self, date: str, time: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM time_slots WHERE date = ? AND time = ?", (date, time))
        self.conn.commit()
        return cursor.rowcount > 0

    def user_has_booking(self, user_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM bookings WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None

    def get_user_booking(self, user_id: int) -> sqlite3.Row | None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

    def get_available_dates(self, days_ahead: int = 30) -> list[str]:
        today = datetime.now().date()
        last_day = today + timedelta(days=days_ahead)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT wd.date
            FROM work_days wd
            JOIN time_slots ts ON ts.date = wd.date
            WHERE wd.is_closed = 0
              AND wd.date BETWEEN ? AND ?
              AND NOT EXISTS (
                  SELECT 1
                  FROM bookings b
                  WHERE b.date = ts.date AND b.time = ts.time
              )
            ORDER BY wd.date
            """,
            (today.isoformat(), last_day.isoformat()),
        )
        return [row["date"] for row in cursor.fetchall()]

    def get_available_slots(self, date: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT ts.time
            FROM time_slots ts
            JOIN work_days wd ON wd.date = ts.date
            WHERE ts.date = ?
              AND wd.is_closed = 0
              AND NOT EXISTS (
                  SELECT 1 FROM bookings b WHERE b.date = ts.date AND b.time = ts.time
              )
            ORDER BY ts.time
            """,
            (date,),
        )
        return [row["time"] for row in cursor.fetchall()]

    def create_booking(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        phone: str,
        date: str,
        time: str,
        reminder_job_id: str | None = None,
    ) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO bookings (
                    user_id, username, full_name, phone, date, time, reminder_job_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    full_name,
                    phone,
                    date,
                    time,
                    reminder_job_id,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_reminder_job_id(self, booking_id: int, job_id: str | None) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE bookings SET reminder_job_id = ? WHERE id = ?",
            (job_id, booking_id),
        )
        self.conn.commit()

    def cancel_booking_by_user(self, user_id: int) -> sqlite3.Row | None:
        booking = self.get_user_booking(user_id)
        if not booking:
            return None
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return booking

    def cancel_booking_by_id(self, booking_id: int) -> sqlite3.Row | None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        booking = cursor.fetchone()
        if not booking:
            return None
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        self.conn.commit()
        return booking

    def get_schedule_for_date(self, date: str) -> list[dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT ts.time, b.id AS booking_id, b.full_name, b.phone, b.user_id
            FROM time_slots ts
            LEFT JOIN bookings b ON b.date = ts.date AND b.time = ts.time
            WHERE ts.date = ?
            ORDER BY ts.time
            """,
            (date,),
        )
        rows = cursor.fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "time": row["time"],
                    "booking_id": row["booking_id"],
                    "full_name": row["full_name"],
                    "phone": row["phone"],
                    "user_id": row["user_id"],
                }
            )
        return result

    def get_bookings_for_restore(self) -> list[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bookings")
        return cursor.fetchall()

    def close(self) -> None:
        self.conn.close()
