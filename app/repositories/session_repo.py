import json
from app.database import get_db

class SessionRepo:
    @staticmethod
    async def save(user_key: str, step: str, data: dict):
        async with get_db() as db:
            await db.execute(
                "INSERT OR REPLACE INTO fsm_sessions (user_key, step, data, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (user_key, step, json.dumps(data))
            )
            await db.commit()

    @staticmethod
    async def load(user_key: str):
        async with get_db() as db:
            async with db.execute("SELECT step, data FROM fsm_sessions WHERE user_key = ?", (user_key,)) as cur:
                row = await cur.fetchone()
                if row:
                    return row["step"], json.loads(row["data"])
                return None, {}

    @staticmethod
    async def delete(user_key: str):
        async with get_db() as db:
            await db.execute("DELETE FROM fsm_sessions WHERE user_key = ?", (user_key,))
            await db.commit()