from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bots.detailing.config import (
    GALLERY_MODE, GALLERY_URL, GALLERY_PHOTOS, EXAMPLES_TEXT, NO_EXAMPLES,
    BOOKING_OFFER, BOOKING_SKIP
)
from app.bots.detailing.handlers.discount_window import start_booking_flow

router = Router()

@router.message(F.text == "📸 Примеры работ")
async def show_examples(message: Message, state: FSMContext):
    if GALLERY_MODE == "album" and GALLERY_URL:
        await message.answer(f"{EXAMPLES_TEXT}\n\n👉 {GALLERY_URL}")
    elif GALLERY_MODE == "gallery" and GALLERY_PHOTOS:
        from aiogram.types import InputMediaPhoto
        media = [InputMediaPhoto(media=url) for url in GALLERY_PHOTOS[:10]]
        await message.answer_media_group(media=media)
        await message.answer(EXAMPLES_TEXT)
    else:
        await message.answer(NO_EXAMPLES)

    builder = InlineKeyboardBuilder()
    builder.button(text=BOOKING_OFFER, callback_data="book_from_examples")
    builder.button(text=BOOKING_SKIP, callback_data="back_to_menu_examples")
    builder.adjust(1)
    await message.answer(
        "Вам понравились наши работы? Запишитесь на консультацию!",
        reply_markup=builder.as_markup()
    )
    await state.update_data(source="examples")

@router.callback_query(F.data == "book_from_examples")
async def book_from_examples(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await start_booking_flow(callback.message, state, is_discount=False)
    await callback.answer()

@router.callback_query(F.data == "back_to_menu_examples")
async def back_to_menu_examples(callback: CallbackQuery, state: FSMContext):
    from app.bots.detailing.keyboards.reply import main_keyboard
    await callback.message.delete()
    await callback.message.answer("Возвращаемся в меню.", reply_markup=main_keyboard())
    await state.clear()
    await callback.answer()