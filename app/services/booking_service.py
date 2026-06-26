from app.database import get_db
from app.repositories.booking_repo import BookingRepo
from app.config import Config

class BookingService:
    @staticmethod
    async def can_book_trial(user_id: int) -> bool:
        paid = await BookingRepo.get_paid_trial(user_id)
        return paid is None

    @staticmethod
    async def create_trial_booking(user_id: int, booking_time: str) -> int:
        return await BookingRepo.create_trial(user_id, booking_time, "pending")

    @staticmethod
    async def confirm_payment(booking_id: int):
        await BookingRepo.update_status(booking_id, "paid")

    @staticmethod
    async def can_reschedule(booking_id: int) -> bool:
        booking = await BookingRepo.get_paid_trial(booking_id)  # но нужно по id, упростим
        # Для brevity: допустим, что у нас есть метод get_booking_by_id
        # Здесь используем заглушку – в реальном коде добавить метод.
        # Пока оставим проверку через cancel_count
        async with get_db() as db:
            async with db.execute("SELECT cancel_count FROM trial_bookings WHERE id = ?", (booking_id,)) as cur:
                row = await cur.fetchone()
                return row and row["cancel_count"] < Config.MAX_RESCHEDULES