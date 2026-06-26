from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def main_menu(has_trial: bool):
    if has_trial:
        buttons = [
            [KeyboardButton("💰 Стоимость абонемента")],
            [KeyboardButton("💳 Реквизиты для оплаты")],
            [KeyboardButton("🤸 Аренда пилона (студии)")],
            [KeyboardButton("📅 Личный кабинет и расписание")],
            [KeyboardButton("❌ Отменить запись")]
        ]
    else:
        buttons = [
            [KeyboardButton("📝 Запись на пробное занятие")],
            [KeyboardButton("💰 Стоимость абонемента")],
            [KeyboardButton("💳 Реквизиты для оплаты")],
            [KeyboardButton("🤸 Аренда пилона (студии)")],
            [KeyboardButton("📅 Личный кабинет и расписание")],
            [KeyboardButton("❌ Отменить запись")]
        ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def menu_button():
    return ReplyKeyboardMarkup([[KeyboardButton("📋 Меню")]], resize_keyboard=True)

def cancel_button():
    return ReplyKeyboardMarkup([[KeyboardButton("❌ Отмена")]], resize_keyboard=True, one_time_keyboard=True)

def cancel_choice_keyboard(can_reschedule_trial: bool):
    buttons = [[KeyboardButton("❌ Отменить занятие (клиент студии)")]]
    if can_reschedule_trial:
        buttons.append([KeyboardButton("❌ Отменить пробное занятие")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)

def cancel_reason_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("⏰ Меньше 12 часов"), KeyboardButton("⏰ Больше 12 часов")]],
        resize_keyboard=True, one_time_keyboard=True
    )