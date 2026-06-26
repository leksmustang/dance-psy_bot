# app/bots/detailing/config.py
# Конфигурация для бота детейлинга (константы, не включая токен)

# --- Демо-информация (показывается в приветствии) ---
DEMO_COMPANY = "QuickBizAuto"
DEMO_NOTICE = "⚠️ Это демонстрационный бот-макет от компании QuickBizAuto. Все функции работают, заявки приходят владельцу бота."

# --- Логотип ---
LOGO_URL = "https://example.com/logo.png"   # Замените на свой URL или file_id

# --- Квиз (прайс) ---
CAR_CATEGORIES = {
    "econom": "🚗 Эконом (Lada, Hyundai, Kia, Renault и др.)",
    "standard": "🚙 Стандарт (Toyota, Honda, Ford, Nissan и др.)",
    "premium": "🏎 Премиум (BMW, Mercedes, Audi, Lexus и др.)"
}

SERVICES = {
    "cleaning": "🧼 Химчистка",
    "polishing": "✨ Полировка",
    "ceramic": "💎 Керамика"
}

PRICE_RANGES = {
    "econom": {"cleaning": (3000, 5000), "polishing": (5000, 7000), "ceramic": (15000, 20000)},
    "standard": {"cleaning": (5000, 8000), "polishing": (7000, 10000), "ceramic": (20000, 30000)},
    "premium": {"cleaning": (8000, 12000), "polishing": (10000, 15000), "ceramic": (30000, 50000)}
}

# --- Запись: мастера и боксы по чётности дня ---
MASTER_EVEN = "Василий"
BOX_EVEN = "Бокс №1"
MASTER_ODD = "Александр"
BOX_ODD = "Бокс №2"

# --- Демо-цены (если не переданы из квиза) ---
DEMO_PRICE_MIN = 3000
DEMO_PRICE_MAX = 50000

# --- Контакты для продажи бота (показываются после успешной записи) ---
SALES_CONTACT = (
    "✨ Хотите ТАКОЙ ЖЕ бот для своего бизнеса?\n\n"
    "Мы — QuickBizAuto — разрабатываем ботов для детейлинга, автосервисов и не только.\n"
    "📞 Свяжитесь с нами:\n"
    "Telegram: @quickbizauto\n"
    "Телефон: +7 (981) 030-84-51\n"
    "Сайт: quickbizauto.com\n\n"
    "Получите индивидуального бота за 3 дня!"
)

# --- Примеры работ ---
GALLERY_MODE = "gallery"   # "album" или "gallery"
GALLERY_URL = ""           # ссылка на альбом, если mode=album
GALLERY_PHOTOS = [         # список ссылок на фото для gallery
    "https://example.com/photo1.jpg",
    "https://example.com/photo2.jpg",
    "https://example.com/photo3.jpg"
]
EXAMPLES_TEXT = "📸 Вот примеры наших работ:"
NO_EXAMPLES = "К сожалению, примеры работ пока не загружены. Загляните позже!"

# --- Тексты сообщений (для кнопок и квиза) ---
START_TEXT = (
    "🚗 Добро пожаловать в демонстрационный бот детейлинг-центра!\n"
    "{demo_notice}\n\n"
    "Здесь вы можете:\n"
    "💰 Узнать стоимость услуг\n"
    "🎁 Записаться на свободное окно со скидкой 15%\n"
    "📸 Посмотреть примеры работ\n\n"
    "После любого действия вы сможете оставить заявку на реальную консультацию.\n"
    "Выберите пункт меню:"
)

ASK_CAR_CATEGORY = "Выберите категорию автомобиля:"
ASK_SERVICE = "Выберите услугу:"
PRICE_RESULT = (
    "💰 Стоимость {service} для {category}:\n"
    "от {min_price} до {max_price} руб.\n\n"
    "Хотите записаться на бесплатную консультацию?"
)

BOOKING_OFFER = "📝 Записаться на консультацию"
BOOKING_SKIP = "🔙 В главное меню"

ASK_NAME = "Введите ваше имя:"
ASK_DATE = "📅 Укажите желаемую дату (ДД.ММ.ГГГГ):"
ASK_TIME = "🕐 Укажите время (ЧЧ:ММ):"

BOOKING_SUCCESS_USER = (
    "✅ {name}, ваша заявка принята!\n\n"
    "📅 Дата: {date}\n"
    "🕐 Время: {time}\n"
    "👨‍🔧 Мастер: {master}\n"
    "📦 {box}\n"
    "💰 Скидка 15% учтена.\n\n"
    "Ориентировочная стоимость: от {price_min} до {price_max} руб.\n\n"
    "Наш менеджер свяжется с вами для подтверждения.\n\n"
    "🔧 Это демонстрационный бот, но заявка реально отправлена владельцу.\n\n"
    "{sales_contact}"
)

BOOKING_SUCCESS_ADMIN = (
    "📩 Новая заявка на запись!\n"
    "Имя: {name}\n"
    "Телефон: {phone}\n"
    "Дата: {date}\nВремя: {time}\n"
    "Мастер: {master}\n{box}\n"
    "Пользователь: @{username} (id: {user_id})"
)