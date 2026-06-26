import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from app.config import Config
from app.bots.psychologist.handlers import router
from app.middlewares.antiflood import AntiFloodMiddleware
import logging

logger = logging.getLogger(__name__)

async def run_psychologist():
    bot = Bot(token=Config.PSY_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()
    dp.message.middleware(AntiFloodMiddleware(limit=2, period=1))

    # Сбрасываем привязку роутера, если он уже был к кому-то привязан
    if hasattr(router, '_parent_router') and router._parent_router is not None:
        router._parent_router = None

    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="cancel", description="Отменить действие"),
        BotCommand(command="manager", description="Связаться с психологом"),
    ])

    logger.info("Психолог бот запущен")
    await dp.start_polling(bot)