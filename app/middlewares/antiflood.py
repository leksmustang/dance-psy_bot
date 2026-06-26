from aiogram import BaseMiddleware
from collections import defaultdict
import time

class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit=2, period=1):
        self.limit = limit
        self.period = period
        self.users = defaultdict(list)

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        now = time.time()
        self.users[user_id] = [t for t in self.users[user_id] if now - t < self.period]
        if len(self.users[user_id]) >= self.limit:
            await event.answer("Слишком много запросов. Подождите немного.")
            return
        self.users[user_id].append(now)
        return await handler(event, data)