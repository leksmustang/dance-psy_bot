import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.config import Config
import logging

logger = logging.getLogger(__name__)

_slots_cache = {}
_cache_ttl = 30

def _get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        Config.PSY_GOOGLE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return build('calendar', 'v3', credentials=creds)

async def get_free_slots():
    now = datetime.now()
    cache_key = now.strftime("%Y%m%d%H")
    if cache_key in _slots_cache and (datetime.now() - _slots_cache[cache_key]['ts']).seconds < _cache_ttl:
        return _slots_cache[cache_key]['slots']

    def _sync_fetch():
        service = _get_calendar_service()
        tz = ZoneInfo(Config.TIMEZONE)
        now_moscow = datetime.now(tz)
        start_date = now_moscow.replace(hour=10, minute=0, second=0, microsecond=0)
        if now_moscow.hour >= 18:
            start_date += timedelta(days=1)
        end_date = start_date + timedelta(days=14)
        time_min = start_date.isoformat()
        time_max = end_date.isoformat()
        events_result = service.events().list(
            calendarId=Config.PSY_GOOGLE_CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        busy = []
        for event in events_result.get('items', []):
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            if start and end:
                busy.append((datetime.fromisoformat(start).astimezone(tz), datetime.fromisoformat(end).astimezone(tz)))
        slots = []
        current = start_date
        while current < end_date:
            if 10 <= current.hour < 18:
                slot_end = current + timedelta(hours=1)
                is_free = True
                for b_start, b_end in busy:
                    if not (slot_end <= b_start or current >= b_end):
                        is_free = False
                        break
                if is_free:
                    slots.append(current)
            current += timedelta(hours=1)
            if current.hour >= 18:
                current = current.replace(hour=10, minute=0) + timedelta(days=1)
        return slots

    slots = await asyncio.to_thread(_sync_fetch)
    _slots_cache[cache_key] = {'ts': datetime.now(), 'slots': slots}
    return slots

_booking_locks = set()

async def book_slot(slot: datetime, user_name: str, user_id: int, service: str) -> bool:
    slot_key = slot.isoformat()
    if slot_key in _booking_locks:
        return False
    _booking_locks.add(slot_key)
    try:
        current_free = await get_free_slots()
        if slot not in current_free:
            return False
        def _sync_create():
            service_obj = _get_calendar_service()
            end_time = slot + timedelta(hours=1)
            event = {
                'summary': f'{service} – {user_name} (@{user_id})',
                'description': f'Клиент: {user_name}\nID: {user_id}',
                'start': {'dateTime': slot.isoformat(), 'timeZone': Config.TIMEZONE},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': Config.TIMEZONE},
            }
            created = service_obj.events().insert(calendarId=Config.PSY_GOOGLE_CALENDAR_ID, body=event).execute()
            return created.get('htmlLink')
        link = await asyncio.to_thread(_sync_create)
        return link is not None
    finally:
        _booking_locks.discard(slot_key)