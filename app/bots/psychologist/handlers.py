import logging
import re
import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config import Config
from app.services.calendar_service import get_free_slots, book_slot
from app.bots.psychologist.keyboards import (
    main_menu, inline_services, service_card, appointment_service_buttons,
    free_keyboard, help_keyboard, slot_keyboard
)
from app.utils.formatters import escape_html

router = Router()
logger = logging.getLogger(__name__)

# ----- Тексты сообщений -----
TEXTS = {
    "individual": (
        "🧘 Индивидуальные сессии\n\n"
        "Разовая сессия (1 час):\n   первая – 3500 ₽, далее – 4000 ₽\n\n"
        "Пакет «6 недель поддержки» – 21 000 ₽\n   (6 сессий + поддержка между встречами)"
    ),
    "mac": (
        "🃏 Разбор на МАК\n\n"
        "Вопрос-Ответ (1 час) – 2500 ₽\n   быстрый ответ на ситуацию.\n\n"
        "Полный разбор запроса (1.5–2.5 часа) – 4500 ₽\n   проработка + коррекция состояния."
    ),
    "lila": (
        "🔮 Лила-чакра\n\n"
        "Индивидуальная работа от 3500 ₽ (обсуждается).\nСейчас тестовый запуск."
    ),
    "method": (
        "📘 Методичка по Энергии\n\n"
        "Большая книга (PDF): теория, практики, схемы.\n💰 от 20 000 до 30 000 ₽"
    ),
    "guides": (
        "📚 Набор из 5 гайдов\n\n"
        "Темы: тревога, восстановление, ресурсное утро, границы, самоподдержка.\n💰 от 20 000 до 30 000 ₽"
    ),
    "free": (
        "🎁 Бесплатный чек-лист\n\n"
        "«Самопомощь и самоподдержка» – 12 шагов.\n\n"
        "1️⃣ Подпишитесь на канал: https://t.me/starlight_our_life\n"
        "2️⃣ Нажмите кнопку «✅ Я подписался»"
    ),
    "help": (
        "❓ Помощь\n\n"
        "• Сессии онлайн (Zoom/Telegram).\n"
        "• Перенос за 24 часа.\n"
        "• При неявке сессия сгорает.\n\n"
        "Свяжитесь с психологом через кнопки ниже."
    )
}

# ----- FSM состояния -----
class AppointmentStates(StatesGroup):
    choosing_slot = State()

class FeedbackState(StatesGroup):
    waiting_for_message = State()

class AdminReviewState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_caption = State()

# ----- Базовые команды -----
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добрый день. Я помощник психолога Яны.\nВыберите раздел в меню ниже.",
        reply_markup=main_menu()
    )

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("Действие отменено.")
    else:
        await message.answer("Нет активного действия для отмены.")

@router.message(Command("manager"))
async def cmd_manager(message: Message, state: FSMContext):
    await state.set_state(FeedbackState.waiting_for_message)
    await message.answer(
        "Напишите ваше сообщение психологу. Мы передадим его в течение часа.\n"
        "Для отмены отправьте /cancel"
    )

# ----- Обработка главного меню -----
@router.message(F.text == "🛍 Услуги и цены")
async def show_services(message: Message):
    await message.answer("Выберите услугу:", reply_markup=inline_services())

@router.message(F.text == "📅 Запись на сессию")
async def appointment_start(message: Message, state: FSMContext):
    await message.answer("Выберите услугу для записи:", reply_markup=appointment_service_buttons())

@router.message(F.text == "📚 Материалы")
async def show_materials(message: Message):
    text = "📚 *Материалы*\n\n• Методичка по Энергии – от 20 000 до 30 000 ₽\n• Набор из 5 гайдов – от 20 000 до 30 000 ₽"
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🎁 Бесплатно")
async def show_free(message: Message):
    await message.answer(TEXTS["free"], reply_markup=free_keyboard())

@router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message):
    reviews_folder = "reviews"
    if not os.path.exists(reviews_folder):
        await message.answer("Пока нет отзывов. Будьте первым!")
        return
    photos = [f for f in os.listdir(reviews_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not photos:
        await message.answer("Пока нет отзывов.")
        return
    photos.sort()  # сортируем для порядка
    batch_size = 10
    for i in range(0, len(photos), batch_size):
        batch = photos[i:i+batch_size]
        media_group = []
        for photo in batch:
            caption = os.path.splitext(photo)[0][:200]  # подпись из имени файла
            photo_path = os.path.join(reviews_folder, photo)
            try:
                media_group.append(
                    InputMediaPhoto(media=FSInputFile(photo_path), caption=caption)
                )
            except Exception as e:
                logger.error(f"Не удалось добавить фото {photo}: {e}")
        if media_group:
            try:
                await message.answer_media_group(media=media_group)
                await asyncio.sleep(0.5)  # задержка между альбомами
            except Exception as e:
                logger.error(f"Ошибка отправки альбома: {e}")
                await message.answer("Не удалось отправить отзывы. Попробуйте позже.")

@router.message(F.text == "❓ Помощь")
async def show_help(message: Message):
    await message.answer(TEXTS["help"], reply_markup=help_keyboard())

# ----- Админ команда для добавления отзыва -----
@router.message(Command("add_review"))
async def cmd_add_review(message: Message, state: FSMContext):
    if message.from_user.id != Config.PSY_ADMIN_ID:
        await message.answer("У вас нет прав для этой команды.")
        return
    await state.set_state(AdminReviewState.waiting_for_photo)
    await message.answer("Пришлите фотографию отзыва (можно с подписью как часть caption).")

@router.message(AdminReviewState.waiting_for_photo, F.photo)
async def review_photo_received(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(file_id=file_id)
    await state.set_state(AdminReviewState.waiting_for_caption)
    await message.answer("Отлично! Теперь отправьте текст отзыва (подпись).")

@router.message(AdminReviewState.waiting_for_caption)
async def review_caption_received(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправьте текст подписи.")
        return
    caption = message.text.strip()
    data = await state.get_data()
    file_id = data['file_id']
    reviews_folder = "reviews"
    os.makedirs(reviews_folder, exist_ok=True)
    safe_caption = re.sub(r'[\\/*?:"<>|]', "", caption[:50])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"review_{timestamp}_{safe_caption}.jpg"
    file_path = os.path.join(reviews_folder, filename)
    file = await message.bot.get_file(file_id)
    await message.bot.download_file(file.file_path, file_path)
    await message.answer(f"✅ Отзыв сохранён как {filename}")
    await state.clear()

# ----- Навигация -----
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Главное меню:", reply_markup=main_menu())
    await callback.answer()

@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Выберите услугу:", reply_markup=inline_services())
    await callback.answer()

# ----- Карточки услуг -----
@router.callback_query(F.data.startswith("service:"))
async def show_service_card(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    text = TEXTS.get(key, "Информация временно недоступна")
    with_appointment = key in ("individual", "mac", "lila")
    with_purchase = key in ("individual", "mac")
    await callback.message.edit_text(text, reply_markup=service_card(key, with_purchase, with_appointment))
    await callback.answer()

@router.callback_query(F.data.startswith("material:"))
async def show_material_card(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    text = TEXTS.get(key, "Информация временно недоступна")
    await callback.message.edit_text(text, reply_markup=service_card(key, with_purchase=False, with_appointment=False))
    await callback.answer()

# ----- Действия с услугами (покупка, уточнение) -----
@router.callback_query(F.data.startswith("buy:"))
async def handle_buy(callback: CallbackQuery):
    await callback.answer("Оплата временно в ручном режиме. Напишите через обратную связь.", show_alert=True)

@router.callback_query(F.data.startswith("ask:"))
async def handle_ask(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Вы можете задать вопрос через раздел «Помощь» → «Обратная связь».")

# ----- Запись на сессию -----
@router.callback_query(F.data.startswith("appoint:"))
async def handle_appoint_from_card(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    service_map = {"individual": "Индивидуальная сессия", "mac": "МАК-разбор", "lila": "Лила-чакра"}
    service_name = service_map.get(key, key)
    await state.update_data(service=service_name)
    await callback.message.answer("Выберите свободный слот (МСК):")
    await show_slots(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("app_service:"))
async def handle_app_service(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":")[1]
    service_names = {"individual": "Индивидуальная сессия", "mac": "МАК-разбор", "lila": "Лила-чакра"}
    await state.update_data(service=service_names[code])
    await callback.message.answer("Выберите свободный слот (МСК):")
    await show_slots(callback.message, state)
    await callback.answer()

async def show_slots(message: Message, state: FSMContext):
    try:
        slots = await get_free_slots()
        if not slots:
            await message.answer("Нет свободных слотов. Попробуйте позже или свяжитесь через обратную связь.")
            await state.clear()
            return
        await state.set_state(AppointmentStates.choosing_slot)
        await message.answer("Доступные даты и время:", reply_markup=slot_keyboard(slots))
    except Exception as e:
        logger.exception(f"Ошибка получения слотов: {e}")
        await message.answer("Ошибка получения слотов. Попробуйте позже.")

@router.callback_query(AppointmentStates.choosing_slot, F.data.startswith("slot:"))
async def handle_slot(callback: CallbackQuery, state: FSMContext):
    slot_iso = callback.data.split(":")[1]
    start_time = datetime.fromisoformat(slot_iso)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=ZoneInfo(Config.TIMEZONE))
    user = callback.from_user
    data = await state.get_data()
    service = data.get("service", "Консультация")
    success = await book_slot(start_time, user.full_name, user.id, service)
    if success:
        await callback.message.answer(
            f"✅ Вы записаны на {service} на {start_time.strftime('%d.%m.%Y %H:%M')} МСК.\n"
            "Оплата после записи – психолог свяжется с вами."
        )
        try:
            await callback.bot.send_message(
                Config.PSY_ADMIN_ID,
                f"📅 Новая запись: {escape_html(user.full_name)} (@{user.username or 'без username'}) – {service} на {start_time.strftime('%d.%m.%Y %H:%M')}"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу: {e}")
    else:
        await callback.message.answer(
            "❌ Ошибка записи. Возможно, слот уже занят. Попробуйте другой или свяжитесь через обратную связь."
        )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_appointment")
async def cancel_slot(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Запись отменена.")
    await callback.answer()

# ----- Бесплатный чек-лист (проверка подписки) -----
@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        member = await callback.bot.get_chat_member(chat_id=Config.PSY_CHANNEL_ID, user_id=user_id)
        if member.status in ("member", "creator", "administrator"):
            text = (
                "🎁 Спасибо за подписку! Вот ваш чек-лист «Самопомощь и самоподдержка»:\n\n"
                "1. Глубокий вдох и выдох.\n"
                "2. Спросите себя: «Что я чувствую прямо сейчас?»\n"
                "3. Назовите 3 вещи, за которые вы благодарны себе.\n"
                "4. Напишите одно доброе сообщение себе.\n"
                "5. Встаньте и потянитесь.\n"
                "6. Сделайте 5 шагов, меняя направление.\n"
                "7. Напомните себе: «Я делаю, что могу».\n"
                "8. Посмотрите на небо или дерево.\n"
                "9. Выпейте стакан воды.\n"
                "10. Запишите одну маленькую победу дня.\n"
                "11. Скажите «стоп» внутреннему критику.\n"
                "12. Улыбнитесь себе в зеркало.\n\n"
                "Скоро появится PDF-версия."
            )
            await callback.message.answer(text)
        else:
            await callback.message.answer("❌ Вы не подписаны. Подпишитесь и нажмите снова.")
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        await callback.message.answer("⚠️ Не удалось проверить подписку. Убедитесь, что вы подписались, и попробуйте ещё раз.")
    await callback.answer()

# ----- Обратная связь (FSM) -----
@router.callback_query(F.data == "feedback")
async def feedback_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FeedbackState.waiting_for_message)
    await callback.message.answer(
        "Напишите ваше сообщение психологу. Мы передадим его в течение часа.\n"
        "Для отмены отправьте /cancel"
    )

@router.message(FeedbackState.waiting_for_message)
async def feedback_message(message: Message, state: FSMContext):
    user = message.from_user
    text = message.text or message.caption
    if not text:
        await message.answer("Пожалуйста, отправьте текст сообщения.")
        return
    try:
        await message.bot.send_message(
            Config.PSY_ADMIN_ID,
            f"📩 Обратная связь от клиента:\n"
            f"Имя: {escape_html(user.full_name)}\n"
            f"Username: @{user.username or 'отсутствует'}\n"
            f"ID: {user.id}\n"
            f"Текст: {escape_html(text)}"
        )
        await message.answer("✅ Спасибо, ваше сообщение отправлено психологу.")
    except Exception as e:
        logger.error(f"Ошибка отправки обратной связи: {e}")
        await message.answer("⚠️ Не удалось отправить сообщение. Попробуйте позже или свяжитесь напрямую.")
    await state.clear()