import re
from typing import Dict

TIME_UNITS: Dict[str, int] = {
    "s": 1,
    "sec": 1,
    "second": 1,
    "m": 60,
    "min": 60,
    "minute": 60,
    "h": 3600,
    "hr": 3600,
    "hour": 3600,
    "d": 86400,
    "day": 86400,
    "w": 604800,
    "week": 604800,
    "mo": 2592000,
    "month": 2592000,
    "y": 31536000,
    "yr": 31536000,
    "year": 31536000,
}

CYRILLIC_MAP: Dict[str, str] = {
    "с": "s",
    "сек": "s",
    "м": "m",
    "мин": "m",
    "ч": "h",
    "час": "h",
    "д": "d",
    "дн": "d",
    "н": "w",
    "нед": "w",
    "мес": "mo",
    "г": "y",
    "лет": "y",
}


async def str_to_seconds(input_string: str) -> int:
    """
    Convert a string describing a time duration to an integer in seconds.

    Supports both Latin and Cyrillic units, along with common full forms.
    If the string contains multiple units, their values are summed up.
    """
    input_string = re.sub(r"[-\s]+", "", input_string.lower())

    for cyr, lat in CYRILLIC_MAP.items():
        input_string = re.sub(rf"\b{cyr}\b", lat, input_string)

    total_seconds = 0
    matches = re.findall(r"(\d+)([a-z]+)", input_string)
    for value, unit in matches:
        if unit in TIME_UNITS:
            total_seconds += int(value) * TIME_UNITS[unit]

    return total_seconds


async def hms(seconds: float) -> str:
    """
    Convert a time in seconds to a human-readable string (e.g. '1h2m3s').

    If the time is less than 1 second, it will be converted to milliseconds.
    """
    if seconds < 1:
        ms = int(seconds * 1000)
        return f"{ms} millisecond{'s' if ms != 1 else ''}"

    units = [
        (604800, "week"),
        (86400, "day"),
        (3600, "hour"),
        (60, "minute"),
        (1, "second"),
    ]

    parts = []
    for unit_secs, unit_name in units:
        if seconds >= unit_secs:
            value = int(seconds // unit_secs)
            seconds %= unit_secs
            parts.append(f"{value} {unit_name}{'s' if value != 1 else ''}")
            if seconds == 0:
                break

    return " ".join(parts)
