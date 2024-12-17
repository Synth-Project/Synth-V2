import re
from typing import Dict

import disnake
from core.misc.color import BasicColors

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


async def generate_mute_list(
    interaction: disnake.ApplicationCommandInteraction,
) -> tuple[list[disnake.Embed], str | None]:
    """
    Generate a list of currently muted members in the guild.

    Args:
        interaction: The interaction context from which the guild is accessed.

    Returns:
        A tuple containing:
            - A list of disnake.Embed objects, each representing a page with muted members.
            - A string message if there are no muted members, otherwise None.
    """
    muted_members = [
        member
        for member in interaction.guild.members
        if not member.bot and member.current_timeout is not None
    ]

    if not muted_members:
        return [], "There are currently no mutes on this server."

    embeds = []
    per_page = 5

    for i in range(0, len(muted_members), per_page):
        embed = disnake.Embed(
            title="<:calendar:1169690539168366712> Active mutes",
            color=BasicColors.DEFAULT,
        )

        for idx, member in enumerate(muted_members[i : i + per_page], start=i + 1):
            timeout = member.current_timeout
            embed.add_field(
                name="",
                value=f"`[{idx}]` **{member.mention}** - "
                f"<t:{round(timeout.timestamp())}:F> "
                f"(<t:{round(timeout.timestamp())}:R>)",
                inline=False,
            )

        embeds.append(embed)

    return embeds, None


async def generate_ban_list(
    interaction: disnake.ApplicationCommandInteraction,
) -> tuple[list[disnake.Embed], str | None]:
    """
    Generate a list of currently banned users in the guild.

    Args:
        interaction: The interaction context from which the guild is accessed.

    Returns:
        A tuple containing:
            - A list of disnake.Embed objects, each representing a page with banned users.
            - A string message if there are no banned users or if permissions are lacking, otherwise None.
    """
    try:
        banned_users = [entry async for entry in interaction.guild.bans()]
    except disnake.Forbidden:
        return [], "I don't have permission to view banned users."

    if not banned_users:
        return [], "There are currently no bans on this server."

    embeds = []
    per_page = 5

    for i in range(0, len(banned_users), per_page):
        embed = disnake.Embed(
            title="<:ban:1169690539168366712> Active bans",
            color=BasicColors.DEFAULT,
        )

        for idx, ban_entry in enumerate(banned_users[i : i + per_page], start=i + 1):
            reason = ban_entry.reason or "No reason provided"
            embed.add_field(
                name="",
                value=f"`[{idx}]` **{ban_entry.user}** (`{ban_entry.user.id}`)\n"
                f"<:list:1169690529643114547> Reason: {reason}",
                inline=False,
            )

        embeds.append(embed)

    return embeds, None
