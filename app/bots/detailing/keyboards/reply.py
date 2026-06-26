from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    buttons = [
        [KeyboardButton(text="💰 Узнать стоимость")],
        [KeyboardButton(text="🎁 Занять свободное окно со скидкой 15%")],
        [KeyboardButton(text="📸 Примеры работ")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)