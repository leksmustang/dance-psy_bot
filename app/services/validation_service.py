import re
from datetime import datetime

def validate_phone(phone: str) -> bool:
    return bool(re.fullmatch(r'^\+?[0-9]{10,15}$', phone.strip()))

def validate_fullname(name: str) -> bool:
    name = name.strip()
    return 5 <= len(name) <= 100

def validate_birthdate(date_str: str) -> bool:
    if not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', date_str):
        return False
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False