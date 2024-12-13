import re

async def str_to_seconds(input_string) -> int:
    units = {
        "s": 1, "с": 1,  # seconds
        "m": 60, "х": 60,  # minutes
        "h": 3600, "г": 3600,  # hours
        "d": 86400, "д": 86400,  # days
        "w": 604800, "т": 604800,  # weeks
        "o": 2592000, "м": 2592000,  # months
        "y": 31536000, "р": 31536000,  # years
    }

    input_string = re.sub(r"[-\s]+", "", input_string.lower())
    input_string = input_string.replace("мес", "o").replace("mo", "o")

    return sum(
        int(num) * units.get(unit, 1)
        for num, unit in re.findall(r"(\d+)([a-zа-я]+)", input_string)
    )

async def hms(sec):
    time_units = [
        (604800, "week", "weeks"),
        (86400, "day", "days"),
        (3600, "hour", "hours"),
        (60, "minute", "minutes"),
        (1, "second", "seconds"),
    ]

    result = " ".join(
        f"{value} {singular if value == 1 else plural}"
        for unit, singular, plural in time_units
        if (value := sec // unit) > 0 and not (sec := sec % unit)
    )

    if not result:
        ms = int(sec * 1000)
        return f"{ms} millisecond{'s' if ms != 1 else ''}"

    return result
