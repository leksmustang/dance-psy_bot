import logging
from app.database import get_db

logger = logging.getLogger(__name__)

class BookingRepo:
    @staticmethod
    async def create_trial(user_id: int, booking_time: str, status: str = "pending") -> int:
        async with get_db() as db:
            try:
                logger.info(f"Создание записи: user_id={user_id}, time={booking_time}, status={status}")
                await db.execute(
                    "INSERT INTO trial_bookings (user_id, booking_time, status) VALUES (?, ?, ?)",
                    (user_id, booking_time, status)
                )
                await db.commit()
                async with db.execute("SELECT last_insert_rowid()") as cur:
                    row = await cur.fetchone()
                    booking_id = row[0]
                    logger.info(f"Запись создана с id={booking_id}")
                    return booking_id
            except Exception as e:
                logger.error(f"Ошибка при создании записи: {e}", exc_info=True)
                raise

    @staticmethod
    async def get_paid_trial(tg_id: int):
        async with get_db() as db:
            try:
                async with db.execute(
                    """SELECT tb.id, tb.booking_time, tb.cancel_count
                       FROM trial_bookings tb
                       JOIN users u ON tb.user_id = u.id
                       WHERE u.tg_id = ? AND tb.status = 'paid'
                       LIMIT 1""",
                    (tg_id,)
                ) as cur:
                    return await cur.fetchone()
            except Exception as e:
                logger.error(f"Ошибка в get_paid_trial: {e}", exc_info=True)
                return None

    @staticmethod
    async def get_active_trial(tg_id: int):
        async with get_db() as db:
            try:
                async with db.execute(
                    """SELECT tb.id, tb.status
                       FROM trial_bookings tb
                       JOIN users u ON tb.user_id = u.id
                       WHERE u.tg_id = ? AND tb.status IN ('pending', 'paid')
                       LIMIT 1""",
                    (tg_id,)
                ) as cur:
                    return await cur.fetchone()
            except Exception as e:
                logger.error(f"Ошибка в get_active_trial: {e}", exc_info=True)
                return None

    @staticmethod
    async def update_status(booking_id: int, status: str):
        async with get_db() as db:
            try:
                await db.execute("UPDATE trial_bookings SET status = ? WHERE id = ?", (status, booking_id))
                await db.commit()
                logger.info(f"Статус заявки {booking_id} обновлён на {status}")
            except Exception as e:
                logger.error(f"Ошибка обновления статуса: {e}", exc_info=True)
                raise

    @staticmethod
    async def increment_cancel_count(booking_id: int):
        async with get_db() as db:
            try:
                await db.execute("UPDATE trial_bookings SET cancel_count = cancel_count + 1 WHERE id = ?", (booking_id,))
                await db.commit()
            except Exception as e:
                logger.error(f"Ошибка увеличения cancel_count: {e}", exc_info=True)
                raise

    @staticmethod
    async def update_booking_time(booking_id: int, new_time: str):
        async with get_db() as db:
            try:
                await db.execute("UPDATE trial_bookings SET booking_time = ? WHERE id = ?", (new_time, booking_id))
                await db.commit()
            except Exception as e:
                logger.error(f"Ошибка обновления времени: {e}", exc_info=True)
                raise