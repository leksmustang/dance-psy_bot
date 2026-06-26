import asyncio
import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
from app.config import Config
from app.bots.studio_tg.handlers import (
    start, menu, price, payment_details, rental_info, personal_area, unknown,
    start_cancellation, cancel_choice, cancel_client_choice, cancel_client_reason,
    cancel_trial_new_date, cancel_conversation_fallback,
    start_booking, cancel_booking_conversation, get_datetime, get_fullname,
    get_phone, get_birthdate, wait_screenshot, check_db, init_db, cancel_global,
    reset_db_if_incompatible
)
from app.bots.studio_tg.conversation import *

logger = logging.getLogger(__name__)

async def run_studio_tg():
    if not Config.STUDIO_TG_TOKEN:
        logger.error("STUDIO_TG_TOKEN не задан в .env")
        return

    # Принудительный сброс БД, если включен флаг
    if Config.RESET_DB_ON_START and os.path.exists(Config.DB_PATH):
        os.remove(Config.DB_PATH)
        logger.info(f"БД удалена по флагу RESET_DB_ON_START: {Config.DB_PATH}")

    # Проверяем и при необходимости удаляем старую несовместимую БД
    reset_db_if_incompatible()

    # Инициализируем таблицы с новой структурой
    await init_db()

    app = ApplicationBuilder().token(Config.STUDIO_TG_TOKEN).build()

    # Регистрация обработчиков главного меню
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 Меню$"), menu))
    app.add_handler(MessageHandler(filters.Regex("^💰 Стоимость абонемента$"), price))
    app.add_handler(MessageHandler(filters.Regex("^💳 Реквизиты для оплаты$"), payment_details))
    app.add_handler(MessageHandler(filters.Regex("^🤸 Аренда пилона \(студии\)$"), rental_info))
    app.add_handler(MessageHandler(filters.Regex("^📅 Личный кабинет и расписание$"), personal_area))

    # Conversation для отмены занятий
    cancel_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❌ Отменить запись$"), start_cancellation)],
        states={
            CANCEL_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_choice)],
            CANCEL_CLIENT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_client_choice)],
            CANCEL_CLIENT_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_client_reason),
                MessageHandler(filters.PHOTO, cancel_client_reason)
            ],
            CANCEL_TRIAL_NEW_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_trial_new_date)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^📋 Меню$"), cancel_conversation_fallback),
            CommandHandler("cancel", cancel_conversation_fallback)
        ],
        allow_reentry=True
    )
    app.add_handler(cancel_conv)

    # Conversation для записи на пробное занятие
    booking_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Запись на пробное занятие$"), start_booking)],
        states={
            GET_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_datetime)],
            GET_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fullname)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GET_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthdate)],
            WAIT_SCREENSHOT: [
                MessageHandler(filters.PHOTO, wait_screenshot),
                MessageHandler(filters.Document.IMAGE, wait_screenshot),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wait_screenshot)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^📋 Меню$"), cancel_booking_conversation),
            CommandHandler("cancel", cancel_booking_conversation)
        ],
        allow_reentry=True
    )
    app.add_handler(booking_conv)

    # Глобальный обработчик на слово "отмена" (вне диалогов)
    app.add_handler(MessageHandler(filters.Regex(r'(?i)отмена'), cancel_global))

    # Команда для администратора
    app.add_handler(CommandHandler("check_db", check_db))

    # Обработчик всего остального
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    # Удаляем старый вебхук
    await app.bot.delete_webhook(drop_pending_updates=True)

    logger.info(f"Telegram студия бот запущен. Путь к БД: {Config.DB_PATH}")

    # Lifecycle
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()