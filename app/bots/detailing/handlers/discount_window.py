import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot
from app.bots.detailing.states.states import DiscountBooking
from app.config import Config
from app.bots.detailing.config import (
    ASK_NAME, ASK_DATE, ASK_TIME,
    BOOKING_SUCCESS_USER, BOOKING_SUCCESS_ADMIN,
    MASTER_EVEN, BOX_EVEN, MASTER_ODD, BOX_ODD,
    DEMO_PRICE_MIN, DEMO_PRICE_MAX, SALES_CONTACT
)
from app.bots.detailing.keyboards.reply import main_keyboard

router = Router()

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)

async def start_booking_flow(message: Message, state: FSMContext, is_discount: bool = True):
    await state.set_state(DiscountBooking.waiting_for_name)
    await state.update_data(is_discount=is_discount)
    await message.answer("📝 Для записи укажите ваше имя:", reply_markup=cancel_kb)

@router.message(F.text == "🎁 Занять свободное окно со скидкой 15%")
async def discount_entry(message: Message, state: FSMContext):
    await start_booking_flow(message, state, is_discount=True)

@router.message(DiscountBooking.waiting_for_name, F.text != "❌ Отмена")
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Имя должно содержать хотя бы 2 буквы.")
        return
    await state.update_data(name=name)
    await state.set_state(DiscountBooking.waiting_for_phone)
    await message.answer("📞 Укажите ваш номер телефона для связи (например, +7 999 123-45-67):", reply_markup=cancel_kb)

@router.message(DiscountBooking.waiting_for_phone, F.text != "❌ Отмена")
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 5:
        await message.answer("Пожалуйста, введите корректный номер телефона.")
        return
    await state.update_data(phone=phone)
    await state.set_state(DiscountBooking.waiting_for_date)
    await message.answer(ASK_DATE, reply_markup=cancel_kb)

@router.message(DiscountBooking.waiting_for_date, F.text != "❌ Отмена")
async def get_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    if not re.match(r'\d{2}\.\d{2}\.\d{4}', date_text):
        await message.answer("Неверный формат. Пример: 18.05.2026")
        return
    try:
        day = int(date_text.split('.')[0])
    except:
        await message.answer("Ошибка в дате. Попробуйте снова.")
        return
    await state.update_data(date=date_text, day=day)
    await state.set_state(DiscountBooking.waiting_for_time)
    await message.answer(ASK_TIME, reply_markup=cancel_kb)

@router.message(DiscountBooking.waiting_for_time, F.text != "❌ Отмена")
async def get_time(message: Message, state: FSMContext, bot: Bot):
    time_text = message.text.strip()
    if not re.match(r'\d{1,2}:\d{2}', time_text):
        await message.answer("Укажите время в формате ЧЧ:ММ, например 14:30")
        return

    data = await state.get_data()
    name = data["name"]
    phone = data.get("phone", "не указан")
    date = data["date"]
    day = data["day"]
    is_discount = data.get("is_discount", True)

    if day % 2 == 0:
        master = MASTER_EVEN
        box = BOX_EVEN
    else:
        master = MASTER_ODD
        box = BOX_ODD

    price_min = data.get("price_min", DEMO_PRICE_MIN)
    price_max = data.get("price_max", DEMO_PRICE_MAX)

    username = message.from_user.username or "нет username"
    user_id = message.from_user.id
    admin_text = BOOKING_SUCCESS_ADMIN.format(
        name=name, phone=phone, date=date, time=time_text,
        master=master, box=box, username=username, user_id=user_id
    )
    # ИСПРАВЛЕНО: используем DETAILING_ADMIN_ID вместо PSY_ADMIN_ID
    await bot.send_message(Config.DETAILING_ADMIN_ID, admin_text)

    user_text = BOOKING_SUCCESS_USER.format(
        name=name, date=date, time=time_text, master=master, box=box,
        price_min=price_min, price_max=price_max, sales_contact=SALES_CONTACT
    )
    await message.answer(user_text, reply_markup=main_keyboard())
    await state.clear()

@router.message(F.text == "❌ Отмена")
async def cancel_booking(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Запись отменена.", reply_markup=main_keyboard())