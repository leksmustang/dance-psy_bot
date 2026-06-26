# Simple Pydantic-like models (optional, for structure)
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    tg_id: Optional[int] = None
    vk_id: Optional[int] = None
    fullname: str = ""
    phone: str = ""
    birthdate: str = ""

@dataclass
class TrialBooking:
    id: int
    user_id: int
    booking_time: str
    status: str
    cancel_count: int