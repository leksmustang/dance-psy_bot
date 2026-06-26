from datetime import datetime
from zoneinfo import ZoneInfo
from app.config import Config

def utc_to_local(dt_utc: datetime) -> datetime:
    tz = ZoneInfo(Config.TIMEZONE)
    return dt_utc.astimezone(tz)