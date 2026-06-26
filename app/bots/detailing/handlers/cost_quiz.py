from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bots.detailing.states.states import CostQuiz
from app.bots.detailing.config import (
    CAR_CATEGORIES, SERVICES, PRICE_RANGES,
    ASK_CAR_CATEGORY, ASK_SERVICE, PRICE_RESULT,
    BOOKING_OFFER, BOOKING_SKIP
)
from app.bots.detailing.handlers.discount_window import start_booking_flow

router = Router()

@router.message(F.text == "💰 Узнать стоимость")
async def start_cost_quiz(message: Message, state: FSMContext):
    await state.set_state(CostQuiz.choosing_car_category)
    builder = InlineKeyboardBuilder()
    for key, name in CAR_CATEGORIES.items():
        builder.button(text=name, callback_data=f"cat_{key}")
    builder.adjust(1)
    await message.answer(ASK_CAR_CATEGORY, reply_markup=builder.as_markup())

@router.callback_query(CostQuiz.choosing_car_category, F.data.startswith("cat_"))
async def category_chosen(callback: CallbackQuery, state: FSMContext):
    category_key = callback.data.split("_")[1]
    await state.update_data(car_category=category_key)
    await state.set_state(CostQuiz.choosing_service)
    builder = InlineKeyboardBuilder()
    for key, name in SERVICES.items():
        builder.button(text=name, callback_data=f"serv_{key}")
    builder.adjust(1)
    await callback.message.edit_text(ASK_SERVICE, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(CostQuiz.choosing_service, F.data.startswith("serv_"))
async def service_chosen(callback: CallbackQuery, state: FSMContext):
    service_key = callback.data.split("_")[1]
    data = await state.get_data()
    category_key = data.get("car_category")
    price_min, price_max = PRICE_RANGES[category_key][service_key]
    category_name = CAR_CATEGORIES[category_key]
    service_name = SERVICES[service_key]

    result_text = PRICE_RESULT.format(
        service=service_name,
        category=category_name,
        min_price=price_min,
        max_price=price_max
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BOOKING_OFFER, callback_data="book_from_quiz")],
        [InlineKeyboardButton(text=BOOKING_SKIP, callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(result_text, reply_markup=kb)
    await state.update_data(price_min=price_min, price_max=price_max)
    await state.set_state(CostQuiz.waiting_for_booking_decision)
    await callback.answer()

@router.callback_query(CostQuiz.waiting_for_booking_decision, F.data == "book_from_quiz")
async def book_from_quiz(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await start_booking_flow(callback.message, state, is_discount=False)
    await callback.answer()

@router.callback_query(CostQuiz.waiting_for_booking_decision, F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    from app.bots.detailing.keyboards.reply import main_keyboard
    await callback.message.delete()
    await callback.message.answer("Возвращаемся в меню.", reply_markup=main_keyboard())
    await state.clear()
    await callback.answer()