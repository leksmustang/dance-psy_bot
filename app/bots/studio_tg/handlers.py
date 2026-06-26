import logging
import sqlite3
import os
import html
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from app.config import Config
from app.repositories.user_repo import UserRepo
from app.repositories.booking_repo import BookingRepo
from app.services.validation_service import validate_phone, validate_fullname, validate_birthdate
from app.bots.studio_tg.keyboards import main_menu, menu_button, cancel_button, cancel_choice_keyboard, cancel_reason_keyboard
from app.bots.studio_tg.conversation import *

logger = logging.getLogger(__name__)

# ================== ТЕКСТЫ ==================
PAYMENT_DETAILS = (
    "💳 *Реквизиты для оплаты пробного занятия:*\n\n"
    "Сумма: 500 руб.\n"
    "Получатель: Стенина Э.О.\n"
    "Номер телефона(СБП): +79993724281\n"
    "Альфа-Банк\n\n"
    "❗ После оплаты пришлите, пожалуйста, скриншот чека (фото) в этот чат."
)
STUDIO_PAYMENT_DETAILS = (
    "🏦 *Реквизиты для оплаты абонементов и разовых занятий:*\n\n"
    "Номер для перевода (СБП): +79993724281\n"
    "Банк: Альфа-Банк\n\n"
    "После оплаты пришлите чек администратору лично:\n"
    "[@Pole_Family_Murino](https://t.me/Pole_Family_Murino)"
)
RENTAL_INFO = (
    "🤸‍♀️ *Аренда пилона и студии*\n\n"
    "В нашей студии есть абонементы на самотренировки:\n"
    "• Утренние самотренировки (10:00, 11:00) — 1600 ₽ (4 занятия)\n"
    "• Дневные самотренировки (15:00, 16:00) — 2400 ₽ (4 занятия)\n\n"
    "❗ Во время самотренировки в зале может находиться до 4 человек.\n\n"
    "🤸‍♂️ *Аренда зала:*\n"
    "• Разовая аренда — 1200 ₽/час\n"
    "• 1000 ₽/час (аренда 2 часа в неделю, оплата на месяц вперёд, договор)\n"
    "• 900 ₽/час (аренда от 3 часов в неделю, оплата на месяц вперёд, договор)\n"
    "• 850 ₽/час (аренда утренних часов 7:00–11:00, любое количество часов в месяц, оплата на месяц вперёд, договор)\n\n"
    "Арендовать можно любое свободное время из расписания до 20:00 на любую дату.\n\n"
    "Для бронирования обращайтесь к администратору: [@Pole_Family_Murino](https://t.me/Pole_Family_Murino)"
)


# ================== ПРОВЕРКА И СБРОС БД ==================
def reset_db_if_incompatible():
    """Проверяет, существует ли БД и имеет ли она нужную структуру.
       Если нет – удаляет файл, чтобы при следующем init_db() он создался заново."""
    db_path = Config.DB_PATH
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Проверяем наличие таблицы users и столбца id
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone() is None:
            conn.close()
            os.remove(db_path)
            logger.info(f"Удалена старая БД (нет таблицы users): {db_path}")
            return
        cur.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cur.fetchall()]
        if 'id' not in columns:
            conn.close()
            os.remove(db_path)
            logger.info(f"Удалена старая БД (нет столбца id в users): {db_path}")
            return
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trial_bookings'")
        if cur.fetchone() is None:
            conn.close()
            os.remove(db_path)
            logger.info(f"Удалена старая БД (нет таблицы trial_bookings): {db_path}")
            return
        # Проверим наличие столбцов в trial_bookings
        cur.execute("PRAGMA table_info(trial_bookings)")
        cols = [col[1] for col in cur.fetchall()]
        required = ['id', 'user_id', 'booking_time', 'status', 'cancel_count']
        if not all(c in cols for c in required):
            conn.close()
            os.remove(db_path)
            logger.info(f"Удалена старая БД (не хватает столбцов в trial_bookings): {db_path}")
            return
        conn.close()
    except Exception as e:
        logger.warning(f"Ошибка при проверке БД: {e}, удаляем на всякий случай")
        if os.path.exists(db_path):
            os.remove(db_path)


# ================== ИНИЦИАЛИЗАЦИЯ БД ==================
async def init_db():
    """Создаёт таблицы с правильной структурой, если их нет."""
    db_path = Config.DB_PATH
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            vk_id INTEGER UNIQUE,
            fullname TEXT NOT NULL,
            phone TEXT,
            birthdate TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trial_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            booking_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            cancel_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cancel_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reason TEXT,
            lesson_datetime TEXT,
            cancel_option TEXT,
            photo_attachment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info(f"База данных инициализирована ({db_path})")


# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def get_user_link(user):
    if user.username:
        return f"[@{user.username}](https://t.me/{user.username})"
    else:
        return f"[пользователь](tg://user?id={user.id})"


# ================== ОБЩИЕ ОБРАБОТЧИКИ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await UserRepo.get_or_create(tg_id=user.id, fullname=user.full_name)
    await update.message.reply_text(
        "🩰 Добро пожаловать в Семью - студию пилона и современного танца!\n\nНажмите кнопку 'Меню', чтобы продолжить.",
        reply_markup=menu_button()
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text("Выберите действие:", reply_markup=main_menu(paid))


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💰 *Прайс-лист танцевальной студии*\n\n"
        "🔹 *Самостоятельные тренировки:*\n"
        "• Утренние (4 занятия) — 1800 ₽\n"
        "• Обычные (4 занятия) — 2600 ₽\n\n"
        "🔹 *Разовые занятия:*\n"
        "• Разовое занятие — 1100 ₽\n\n"
        "🔹 *Групповые абонементы:*\n"
        "• 4 занятия (30 дней) — 3900 ₽\n"
        "• 8 занятий (30 дней) — 6900 ₽\n\n"
        "🔹 *Групповые + самотренировки:*\n"
        "• 12 занятий (40 дней) — 9900 ₽ (+4 самост. тренировки в подарок)\n"
        "• 16 занятий (60 дней) — 12800 ₽ (+4 самост. тренировки в подарок)\n"
        "• 24 занятия (60 дней) — 19000 ₽ (+4 самост. тренировки в подарок)\n\n"
        "По всем вопросам обращайтесь к администратору: [@Pole_Family_Murino](https://t.me/Pole_Family_Murino)"
    )
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu(paid))


async def payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text(STUDIO_PAYMENT_DETAILS, parse_mode="Markdown", reply_markup=main_menu(paid))


async def rental_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text(RENTAL_INFO, parse_mode="Markdown", reply_markup=main_menu(paid))


async def personal_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Открыть расписание и личный кабинет", url=Config.STUDIO_WIDGET_URL)]])
    await update.message.reply_text(
        "🗓 *Расписание и личный кабинет*\n\nНажмите на кнопку ниже, чтобы перейти к расписанию:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await update.message.reply_text("Главное меню:", reply_markup=main_menu(paid))


# ================== ГЛОБАЛЬНАЯ ОТМЕНА ==================
async def cancel_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает любое сообщение с 'отмена' вне диалога."""
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text(
        "❌ Действие отменено. Возвращаемся в меню.",
        reply_markup=main_menu(paid)
    )
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and "отмена" in update.message.text.lower():
        return await cancel_global(update, context)
    await update.message.reply_text("Пожалуйста, используйте кнопки меню. Нажмите 'Меню' для начала.")


# -------------------- ОТМЕНА ЗАНЯТИЙ --------------------
async def start_cancellation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    trial_booking = await BookingRepo.get_paid_trial(user_id)
    can_reschedule = trial_booking is not None and trial_booking["cancel_count"] < Config.MAX_RESCHEDULES
    await update.message.reply_text(
        "Выберите, что хотите отменить:",
        reply_markup=cancel_choice_keyboard(can_reschedule)
    )
    return CANCEL_CHOICE


async def cancel_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    if "Отменить занятие (клиент студии)" in text:
        await update.message.reply_text("Укажите, за сколько часов до занятия вы отменяете?", reply_markup=cancel_reason_keyboard())
        return CANCEL_CLIENT_CHOICE
    elif "Отменить пробное занятие" in text:
        trial_booking = await BookingRepo.get_paid_trial(user_id)
        if not trial_booking:
            await update.message.reply_text("У вас нет активной записи на пробное занятие.", reply_markup=main_menu(False))
            return ConversationHandler.END
        context.user_data['trial_booking_id'] = trial_booking["id"]
        old_datetime = trial_booking["booking_time"]
        old_dt = datetime.fromisoformat(old_datetime)
        context.user_data['old_trial_datetime'] = old_dt.strftime("%d.%m.%Y в %H:%M")
        context.user_data['current_reschedule_count'] = trial_booking["cancel_count"]
        await update.message.reply_text(
            f"📌 *Пробное занятие можно перенести {Config.MAX_RESCHEDULES} раз(а).*\n\n"
            "Пожалуйста, выберите новую дату и время для переноса занятия из расписания:\n"
            f"{Config.STUDIO_WIDGET_URL}\n\n"
            "Напишите новую дату и время в формате `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
            "Например: 25.05.2026 18:30\n\n"
            "Если передумали, нажмите '❌ Отмена'.",
            parse_mode="Markdown",
            reply_markup=cancel_button()
        )
        return CANCEL_TRIAL_NEW_DATE
    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.")
        return CANCEL_CHOICE


async def cancel_client_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    if "Меньше 12 часов" in text:
        await update.message.reply_text(
            "📝 *Причина отмены занятия*\n\n"
            "Пожалуйста, напишите причину, по которой вы не можете прийти на занятие.\n"
            "Если у вас есть справка, подтверждающая болезнь, пришлите её фото в этот чат.\n\n"
            "Вся информация будет передана администратору.\n\n"
            "Чтобы отменить действие, нажмите '❌ Отмена'.",
            parse_mode="Markdown",
            reply_markup=cancel_button()
        )
        return CANCEL_CLIENT_REASON
    elif "Больше 12 часов" in text:
        script = (
            "📋 *Как отменить запись на занятие (больше 12 часов):*\n\n"
            "1. В личном кабинете нажмите на кнопку *'Вы записаны на занятие'*\n"
            "2. Откроется Ваш профиль клиента. Перейдите во вкладку *'Запись'*.\n"
            "3. Выберите занятие, которое хотели бы отменить. Нажмите кнопку *'Отписаться'*.\n"
            "4. Подтвердите отмену записи.\n\n"
            "✅ *Готово.* Вы успешно отписались от занятия ✨\n\n"
            "Если возникли трудности, обратитесь к администратору:\n"
            "[@Pole_Family_Murino](https://t.me/Pole_Family_Murino)"
        )
        paid = await BookingRepo.get_paid_trial(user_id) is not None
        await update.message.reply_text(script, parse_mode="Markdown", reply_markup=main_menu(paid))
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.")
        return CANCEL_CLIENT_CHOICE


async def cancel_client_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_link = f"[{html.escape(user.full_name)}](tg://user?id={user_id})"

    if update.message.text:
        text = update.message.text.strip()
        if "отмена" in text.lower():
            paid = await BookingRepo.get_paid_trial(user_id) is not None
            await update.message.reply_text("❌ Отмена действия. Возвращаемся в меню.", reply_markup=main_menu(paid))
            return ConversationHandler.END
        reason = text
        admin_text = f"🔔 *Отмена занятия (менее 12 часов)*\n\nКлиент: {user_link}\nПричина: {reason}\nСправки: не приложены"
        await context.bot.send_message(chat_id=Config.STUDIO_TG_ADMIN, text=admin_text, parse_mode="Markdown")
        paid = await BookingRepo.get_paid_trial(user_id) is not None
        await update.message.reply_text(
            "✅ Ваша причина отмены передана администратору.\n\n"
            "Если у вас есть справка, вы можете приложить её сейчас (фото). Или нажмите 'Меню'.",
            reply_markup=main_menu(paid)
        )
        context.user_data['waiting_for_sick_leave'] = True
        context.user_data['reason_text'] = reason
        return WAIT_SCREENSHOT
    elif update.message.photo:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        reason = context.user_data.get('reason_text', 'Не указана')
        admin_text = f"🔔 *Отмена занятия (менее 12 часов)*\n\nКлиент: {user_link}\nПричина: {reason}\nСправка приложена ниже."
        await context.bot.send_photo(chat_id=Config.STUDIO_TG_ADMIN, photo=photo_file.file_id, caption=admin_text, parse_mode="Markdown")
        paid = await BookingRepo.get_paid_trial(user_id) is not None
        await update.message.reply_text("✅ Справка передана администратору. Спасибо!", reply_markup=main_menu(paid))
        context.user_data.pop('waiting_for_sick_leave', None)
        context.user_data.pop('reason_text', None)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, напишите причину отмены текстом.")
        return CANCEL_CLIENT_REASON


async def cancel_trial_new_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    user_link = f"[{html.escape(user.full_name)}](tg://user?id={user_id})"

    if "отмена" in text.lower():
        paid = await BookingRepo.get_paid_trial(user_id) is not None
        await update.message.reply_text("❌ Перенос отменён.", reply_markup=main_menu(paid))
        return ConversationHandler.END

    try:
        datetime_obj = datetime.strptime(text, "%d.%m.%Y %H:%M")
        new_datetime_str = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
        new_datetime_display = datetime_obj.strftime("%d.%m.%Y в %H:%M")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат. Пожалуйста, напишите дату и время в формате:\n`ДД.ММ.ГГГГ ЧЧ:ММ`\n\nНапример: 25.05.2026 18:30",
            parse_mode="Markdown"
        )
        return CANCEL_TRIAL_NEW_DATE

    trial_booking_id = context.user_data.get('trial_booking_id')
    old_datetime_display = context.user_data.get('old_trial_datetime', 'неизвестно')
    current_count = context.user_data.get('current_reschedule_count', 0)
    new_count = current_count + 1

    if trial_booking_id:
        await BookingRepo.update_booking_time(trial_booking_id, new_datetime_str)
        await BookingRepo.increment_cancel_count(trial_booking_id)

    admin_text = f"🔄 *Перенос пробного занятия*\n\nКлиент: {user_link}\nСтарая дата: {old_datetime_display}\nНовая дата: {new_datetime_display}\nПеренос №{new_count} из {Config.MAX_RESCHEDULES}"
    await context.bot.send_message(chat_id=Config.STUDIO_TG_ADMIN, text=admin_text, parse_mode="Markdown")
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text(
        f"✅ Ваше пробное занятие перенесено на {new_datetime_display}.\n\n"
        "Мы уведомили администратора. Ждём вас!\n\nВернуться в меню: нажмите 'Меню'.",
        reply_markup=main_menu(paid)
    )
    return ConversationHandler.END


async def cancel_conversation_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text("❌ Действие отменено.", reply_markup=main_menu(paid))
    return ConversationHandler.END


# -------------------- ЗАПИСЬ НА ПРОБНОЕ --------------------
async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active = await BookingRepo.get_active_trial(user_id)
    if active:
        await update.message.reply_text(
            "❌ У вас уже есть активная запись (оплаченная или ожидающая оплаты). "
            "Дождитесь её завершения или отмените через раздел '❌ Отменить запись'.",
            reply_markup=main_menu(True)
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"📅 Для выбора даты и времени занятия перейдите по ссылке:\n{Config.STUDIO_WIDGET_URL}\n\n"
        "После того как вы выбрали удобное время, напишите сюда дату и время в формате:\n"
        "`ДД.ММ.ГГГГ ЧЧ:ММ`\n\nНапример: 25.05.2026 18:30\n\n"
        "Если передумали, нажмите '❌ Отмена'.",
        parse_mode="Markdown",
        reply_markup=cancel_button()
    )
    return GET_DATETIME


async def cancel_booking_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    booking_id = context.user_data.get('booking_id')
    if booking_id:
        await BookingRepo.update_status(booking_id, "cancelled")
    user_id = update.effective_user.id
    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text("❌ Запись отменена.", reply_markup=main_menu(paid))
    return ConversationHandler.END


async def get_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "отмена" in text.lower():
        return await cancel_booking_conversation(update, context)
    try:
        datetime_obj = datetime.strptime(text, "%d.%m.%Y %H:%M")
        context.user_data['booking_datetime'] = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
        context.user_data['booking_datetime_display'] = datetime_obj.strftime("%d.%m.%Y в %H:%M")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат. Пожалуйста, напишите дату и время в формате:\n`ДД.ММ.ГГГГ ЧЧ:ММ`\n\nНапример: 25.05.2026 18:30",
            parse_mode="Markdown"
        )
        return GET_DATETIME
    await update.message.reply_text("Отлично! Теперь напишите ваши ФИО полностью:")
    return GET_FULLNAME


async def get_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fullname = update.message.text.strip()
    if "отмена" in fullname.lower():
        return await cancel_booking_conversation(update, context)
    if not validate_fullname(fullname):
        await update.message.reply_text("❌ ФИО должно быть не короче 5 символов. Попробуйте ещё раз:")
        return GET_FULLNAME
    context.user_data['fullname'] = fullname
    await update.message.reply_text("Укажите ваш номер телефона для связи (можно с +7 или 8):")
    return GET_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if "отмена" in phone.lower():
        return await cancel_booking_conversation(update, context)
    if not validate_phone(phone):
        await update.message.reply_text("❌ Неверный формат телефона. Укажите номер (10-15 цифр, возможно с +):")
        return GET_PHONE
    context.user_data['phone'] = phone
    await update.message.reply_text("Укажите вашу дату рождения в формате `ДД.ММ.ГГГГ`\nНапример: 15.03.1990", parse_mode="Markdown")
    return GET_BIRTHDATE


async def get_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Начало get_birthdate для пользователя {update.effective_user.id}")
    birthdate_text = update.message.text.strip()
    if "отмена" in birthdate_text.lower():
        return await cancel_booking_conversation(update, context)
    if not validate_birthdate(birthdate_text):
        await update.message.reply_text("❌ Неверный формат. Введите дату рождения в формате `ДД.ММ.ГГГГ`", parse_mode="Markdown")
        return GET_BIRTHDATE
    context.user_data['birthdate'] = birthdate_text

    user_id = update.effective_user.id
    fullname = context.user_data['fullname']
    phone = context.user_data['phone']
    datetime_str = context.user_data['booking_datetime']

    # Сохраняем пользователя
    user = await UserRepo.get_or_create(tg_id=user_id, fullname=fullname, phone=phone, birthdate=birthdate_text)
    logger.info(f"Получен пользователь: {user}")
    if not user or not user.get('id'):
        logger.error("Не удалось создать или найти пользователя")
        await update.message.reply_text("❌ Ошибка создания пользователя. Попробуйте позже.")
        return ConversationHandler.END

    # Создаём запись
    booking_id = await BookingRepo.create_trial(user["id"], datetime_str, "pending")
    if not booking_id:
        logger.error("Не удалось создать запись")
        await update.message.reply_text("❌ Ошибка создания записи. Попробуйте позже.")
        return ConversationHandler.END

    context.user_data['booking_id'] = booking_id
    logger.info(f"Создана заявка #{booking_id} для пользователя {user_id}")

    # Сразу скрываем кнопку записи
    await update.message.reply_text(
        "🔄 Вы создали заявку на пробное занятие. Ожидайте подтверждения.",
        reply_markup=main_menu(True)
    )

    await update.message.reply_text(PAYMENT_DETAILS, parse_mode="Markdown", reply_markup=cancel_button())
    await update.message.reply_text("💡 После оплаты пришлите, пожалуйста, скриншот чека (фото).\nЕсли вы не оплатили, нажмите '❌ Отмена'.")
    return WAIT_SCREENSHOT


# ================== ОБРАБОТКА СКРИНШОТА ==================
async def wait_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=== wait_screenshot called ===")
    user = update.effective_user
    user_id = user.id
    booking_id = context.user_data.get('booking_id')

    # Обработка ожидания справки (для отмены занятия)
    if context.user_data.get('waiting_for_sick_leave'):
        if update.message.photo:
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            reason = context.user_data.get('reason_text', 'Не указана')
            user_link = f"[{html.escape(user.full_name)}](tg://user?id={user_id})"
            admin_text = f"🔔 *Отмена занятия (менее 12 часов)*\n\nКлиент: {user_link}\nПричина: {reason}\nСправка приложена ниже."
            await context.bot.send_photo(chat_id=Config.STUDIO_TG_ADMIN, photo=photo_file.file_id, caption=admin_text, parse_mode="Markdown")
            paid = await BookingRepo.get_paid_trial(user_id) is not None
            await update.message.reply_text("✅ Справка передана администратору. Спасибо!", reply_markup=main_menu(paid))
            context.user_data.pop('waiting_for_sick_leave', None)
            context.user_data.pop('reason_text', None)
            return ConversationHandler.END
        else:
            await update.message.reply_text("Пожалуйста, пришлите фото справки или нажмите 'Меню'.")
            return WAIT_SCREENSHOT

    # --- Обработка чека (фото или документ-изображение) ---
    file_obj = None
    is_document = False

    if update.message.photo:
        file_obj = update.message.photo[-1]
        is_document = False
    elif (update.message.document and update.message.document.mime_type and 
          update.message.document.mime_type.startswith('image/')):
        file_obj = update.message.document
        is_document = True
    elif update.message.text:
        text = update.message.text.strip()
        if "отмена" in text.lower():
            return await cancel_booking_conversation(update, context)
        else:
            await update.message.reply_text("Пожалуйста, пришлите именно фотографию чека.\nИли нажмите '❌ Отмена'.", reply_markup=cancel_button())
            return WAIT_SCREENSHOT
    else:
        await update.message.reply_text("Пожалуйста, пришлите скриншот чека в виде фотографии или изображения.\nИли нажмите '❌ Отмена'.", reply_markup=cancel_button())
        return WAIT_SCREENSHOT

    # Скачиваем файл
    try:
        if is_document:
            file = await file_obj.get_file()
            file_path = f"temp_{user_id}.jpg"
            await file.download_to_drive(file_path)
            file_id = file_obj.file_id
        else:
            photo = file_obj
            file = await photo.get_file()
            file_path = f"temp_{user_id}.jpg"
            await file.download_to_drive(file_path)
            file_id = photo.file_id
    except Exception as e:
        logger.error(f"Ошибка скачивания файла: {e}")
        await update.message.reply_text("⚠️ Не удалось загрузить файл. Попробуйте ещё раз.")
        return WAIT_SCREENSHOT

    # Обновляем статус бронирования
    if booking_id:
        await BookingRepo.update_status(booking_id, "paid")
        logger.info(f"Статус заявки #{booking_id} обновлён на 'paid'")
    else:
        logger.error("booking_id отсутствует в context.user_data")

    fullname = context.user_data.get('fullname', 'Не указано')
    phone = context.user_data.get('phone', 'Не указано')
    birthdate = context.user_data.get('birthdate', 'Не указана')
    datetime_display = context.user_data.get('booking_datetime_display', 'Не указано')
    user_link = f"[{html.escape(user.full_name)}](tg://user?id={user_id})"

    admin_text = (
        f"✅ *Новая оплаченная запись на пробное занятие!*\n\n"
        f"Клиент: {fullname} {user_link}\n"
        f"Телефон: {phone}\n"
        f"Дата рождения: {birthdate}\n"
        f"Дата и время: {datetime_display}\n"
        f"Номер заявки: {booking_id}"
    )

    try:
        await context.bot.send_photo(
            chat_id=Config.STUDIO_TG_ADMIN,
            photo=file_id,
            caption=admin_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки фото админу: {e}")
        await update.message.reply_text("⚠️ Не удалось отправить чек администратору, но запись сохранена. Мы свяжемся с вами.")

    # Удаляем временный файл
    try:
        os.remove(file_path)
    except:
        pass

    paid = await BookingRepo.get_paid_trial(user_id) is not None
    await update.message.reply_text(
        "✅ Спасибо! Ваша запись подтверждена, а скриншот оплаты передан администратору.\n"
        "Мы свяжемся с вами в ближайшее время для подтверждения.\n\n"
        "Вернуться в меню: нажмите '📋 Меню'.",
        reply_markup=main_menu(paid)
    )
    return ConversationHandler.END


# -------------------- КОМАНДА ДЛЯ АДМИНИСТРАТОРА (проверка БД) --------------------
async def check_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != Config.STUDIO_TG_ADMIN:
        await update.message.reply_text("⛔ Только для администратора.")
        return
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT tb.id, tb.booking_time, u.fullname, u.phone, tb.status
            FROM trial_bookings tb
            LEFT JOIN users u ON tb.user_id = u.id
            ORDER BY tb.id
        """)
        rows = cur.fetchall()
        conn.close()
        if not rows:
            await update.message.reply_text("📭 В базе нет заявок.")
            return
        text = "📋 *Все заявки:*\n\n"
        for row in rows:
            text += f"#{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}\n"
            if len(text) > 3800:
                await update.message.reply_text(text, parse_mode="Markdown")
                text = ""
        if text:
            await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}")