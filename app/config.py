import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Psychologist
    PSY_BOT_TOKEN = os.getenv("PSY_BOT_TOKEN")
    PSY_CHANNEL_ID = os.getenv("PSY_CHANNEL_ID")
    PSY_ADMIN_ID = int(os.getenv("PSY_ADMIN_ID", 0))
    PSY_GOOGLE_CALENDAR_ID = os.getenv("PSY_GOOGLE_CALENDAR_ID")
    PSY_GOOGLE_CREDENTIALS_FILE = os.getenv("PSY_GOOGLE_CREDENTIALS_FILE")
    PSYCHOLOGIST_USERNAME = os.getenv("PSYCHOLOGIST_USERNAME")

    # Studio Telegram
    STUDIO_TG_TOKEN = os.getenv("STUDIO_TG_TOKEN")
    STUDIO_TG_ADMIN = int(os.getenv("STUDIO_TG_ADMIN", 0))
    STUDIO_WIDGET_URL = os.getenv("STUDIO_WIDGET_URL")

    

    # Common
    TRIAL_PRICE = int(os.getenv("TRIAL_PRICE", 500))
    MAX_RESCHEDULES = int(os.getenv("MAX_RESCHEDULES", 1))
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DB_PATH = os.getenv("DB_PATH", "dance_studio.db")
    RESET_DB_ON_START = os.getenv("RESET_DB_ON_START", "false").lower() == "true"

    # Detailing bot
    DETAILING_BOT_TOKEN = os.getenv("DETAILING_BOT_TOKEN")
    DETAILING_ADMIN_ID = int(os.getenv("DETAILING_ADMIN_ID", 0))