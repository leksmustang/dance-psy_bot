import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.config import Config
from app.bots.detailing.handlers import start, cost_quiz, discount_window, examples

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_detailing_bot():
    bot = Bot(
        token=Config.DETAILING_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()

    # Сброс привязки для каждого роутера перед включением
    for router in [start.router, cost_quiz.router, discount_window.router, examples.router]:
        if hasattr(router, '_parent_router') and router._parent_router is not None:
            router._parent_router = None
        dp.include_router(router)

    logger.info("Детейлинг бот запущен")
    await dp.start_polling(bot)