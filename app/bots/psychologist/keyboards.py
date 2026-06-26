from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.config import Config

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛍 Услуги и цены")],
        [KeyboardButton(text="📅 Запись на сессию")],
        [KeyboardButton(text="📚 Материалы")],
        [KeyboardButton(text="🎁 Бесплатно")],
        [KeyboardButton(text="⭐ Отзывы")],
        [KeyboardButton(text="❓ Помощь")],
    ], resize_keyboard=True)

# Остальные функции без изменений
def inline_services():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Индивидуальные сессии", callback_data="service:individual")],
        [InlineKeyboardButton(text="Разбор на МАК", callback_data="service:mac")],
        [InlineKeyboardButton(text="Лила-чакра", callback_data="service:lila")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
    ])

def service_card(product_key: str, with_purchase=True, with_appointment=False):
    buttons = []
    if with_purchase:
        buttons.append([InlineKeyboardButton(text="💰 Купить", callback_data=f"buy:{product_key}")])
    if with_appointment:
        buttons.append([InlineKeyboardButton(text="📅 Записаться", callback_data=f"appoint:{product_key}")])
    buttons.append([InlineKeyboardButton(text="❓ Уточнить", callback_data=f"ask:{product_key}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_services")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def appointment_service_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Индивидуальная сессия", callback_data="app_service:individual")],
        [InlineKeyboardButton(text="МАК-разбор", callback_data="app_service:mac")],
        [InlineKeyboardButton(text="Лила-чакра", callback_data="app_service:lila")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def free_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def help_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Обратная связь", callback_data="feedback")],
        [InlineKeyboardButton(text="📞 Контакт психолога", url=f"https://t.me/{Config.PSYCHOLOGIST_USERNAME}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def slot_keyboard(slots):
    kb = []
    for slot in slots[:12]:
        kb.append([InlineKeyboardButton(text=slot.strftime("%d.%m %H:%M"), callback_data=f"slot:{slot.isoformat()}")])
    kb.append([InlineKeyboardButton(text="Отмена", callback_data="cancel_appointment")])
    return InlineKeyboardMarkup(inline_keyboard=kb)