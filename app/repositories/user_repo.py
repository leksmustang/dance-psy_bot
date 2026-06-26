import logging
from app.database import get_db

logger = logging.getLogger(__name__)

class UserRepo:
    @staticmethod
    async def get_or_create(tg_id=None, vk_id=None, fullname=None, phone=None, birthdate=None):
        async with get_db() as db:
            try:
                if tg_id:
                    async with db.execute("SELECT id, fullname, phone, birthdate FROM users WHERE tg_id = ?", (tg_id,)) as cur:
                        row = await cur.fetchone()
                        if row:
                            logger.info(f"Найден существующий пользователь с tg_id={tg_id}, id={row['id']}")
                            return dict(row)
                elif vk_id:
                    async with db.execute("SELECT id, fullname, phone, birthdate FROM users WHERE vk_id = ?", (vk_id,)) as cur:
                        row = await cur.fetchone()
                        if row:
                            return dict(row)

                # Вставка нового пользователя
                await db.execute(
                    "INSERT INTO users (tg_id, vk_id, fullname, phone, birthdate) VALUES (?, ?, ?, ?, ?)",
                    (tg_id, vk_id, fullname, phone, birthdate)
                )
                await db.commit()  # явный коммит
                async with db.execute("SELECT last_insert_rowid()") as cur:
                    row = await cur.fetchone()
                    new_id = row[0]
                    logger.info(f"Создан новый пользователь с id={new_id}, tg_id={tg_id}")
                return {"id": new_id, "fullname": fullname, "phone": phone, "birthdate": birthdate}
            except Exception as e:
                logger.error(f"Ошибка в get_or_create: {e}", exc_info=True)
                # Если произошла ошибка, пробуем найти пользователя повторно (на случай race condition)
                if tg_id:
                    async with db.execute("SELECT id, fullname, phone, birthdate FROM users WHERE tg_id = ?", (tg_id,)) as cur:
                        row = await cur.fetchone()
                        if row:
                            logger.info(f"Найден пользователь после ошибки: id={row['id']}")
                            return dict(row)
                raise  # если не нашли, пробрасываем исключение выше