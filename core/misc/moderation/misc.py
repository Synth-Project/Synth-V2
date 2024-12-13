import re
from typing import Dict

TIME_UNITS: Dict[str, int] = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "mo": 2592000,
    "y": 31536000,
}


async def str_to_seconds(input_string: str) -> int:
    """
    Convert a string describing a time to an integer in seconds.

    The string can use the following units: s, m, h, d, w, mo, y.
    The string can also use the following Cyrillic units: с, х, г, д, т, м, р.
    The string can also use the following English units: second, minute, hour, day, week, month, year.

    If the string contains multiple units, they are added together.
    """
    input_string = re.sub(r"[-\s]+", "", input_string.lower())
    input_string = input_string.replace("month", "mo").replace("мес", "mo")

    cyrillic_map = {
        "с": "s",
        "х": "m",
        "г": "h",
        "д": "d",
        "т": "w",
        "м": "mo",
        "р": "y",
    }
    for cyr, lat in cyrillic_map.items():
        input_string = input_string.replace(cyr, lat)

    total = 0
    matches = re.findall(r"(\d+)([a-z]+)", input_string)
    for value, unit in matches:
        if unit in TIME_UNITS:
            total += int(value) * TIME_UNITS[unit]
    return total


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
