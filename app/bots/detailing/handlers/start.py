from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.bots.detailing.keyboards.reply import main_keyboard
from app.bots.detailing.config import LOGO_URL, START_TEXT, DEMO_NOTICE

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    text = START_TEXT.format(demo_notice=DEMO_NOTICE)
    try:
        await message.answer_photo(
            photo=LOGO_URL,
            caption=text,
            reply_markup=main_keyboard()
        )
    except Exception:
        await message.answer(text, reply_markup=main_keyboard())