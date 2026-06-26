from app.database import get_db

class CancelRepo:
    @staticmethod
    async def create_request(user_id: int, reason: str, lesson_datetime: str, cancel_option: str, photo: str = None):
        async with get_db() as db:
            await db.execute(
                "INSERT INTO cancel_requests (user_id, reason, lesson_datetime, cancel_option, photo_attachment) VALUES (?, ?, ?, ?, ?)",
                (user_id, reason, lesson_datetime, cancel_option, photo)
            )
            await db.commit()