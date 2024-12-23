import re
from typing import Dict, Optional

import disnake
from core.misc.color import BasicColors

from core.database.models.warns import WarnsModel
from core.misc.embed import CustomEmbed

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

SIMPLIFIED_TIME_UNITS = {
    "second",
    "minute",
    "hour",
    "day",
    "week",
    "month",
    "year",
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


async def hms(seconds: float, to_list: bool = False) -> str | list[str]:
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

    if to_list:
        return parts

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
        return [], "Currenly, there are no mutes on the server."

    per_page = 5

    embeds = [
        disnake.Embed(
            title="<:calendar:1169690539168366712> Active mutes",
            color=BasicColors.DEFAULT,
        ).add_field(
            name="",
            value=(
                f"`[{idx}]` **{member.mention}** - "
                f"<t:{round(member.current_timeout.timestamp())}:F> "
                f"(<t:{round(member.current_timeout.timestamp())}:R>)"
            ),
            inline=False,
        )
        for i in range(0, len(muted_members), per_page)
        for idx, member in enumerate(muted_members[i : i + per_page], start=i + 1)
    ]

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
        return [], "I don't have required permission to view banned users."

    if not banned_users:
        return [], "Currently, there are not bans on the server."

    per_page = 5

    embeds = [
        disnake.Embed(
            title="<:ban:1169690539168366712> Active bans",
            color=BasicColors.DEFAULT,
        ).add_field(
            name="",
            value=(
                f"`[{idx}]` **{ban_entry.user}** (`{ban_entry.user.id}`)\n"
                f"- **Reason:** {ban_entry.reason or 'No reason provided'}"
            ),
            inline=False,
        )
        for i in range(0, len(banned_users), per_page)
        for idx, ban_entry in enumerate(banned_users[i : i + per_page], start=i + 1)
    ]

    return embeds, None


async def generate_warns_list(
    interaction: disnake.ApplicationCommandInteraction,
    warns: Optional[list[WarnsModel]],
) -> tuple[list[disnake.Embed], str | None]:
    """
    Generate a list of currently warned users in the guild.

    Args:
        interaction: The interaction context from which the guild is accessed.

    Returns:
        A tuple containing:
            - A list of disnake.Embed objects, each representing a page with warned users.
            - A string message if there are no warned users, otherwise None.
    """
    if not warns:
        embed = CustomEmbed(
            title="<:info:1169685342077583480> User Warns",
            description="Currently, there are no warns on the server.",
        ).get_embed()

        return await interaction.send(embed=embed)

    warn_pages = [
        CustomEmbed(
            title=f"<:info:1169685342077583480> Warn #{warn.id}",
            description=(
                f"**Member:** {member.mention} ({member})\n"
                f"**Administrator:** {moderator.mention} ({moderator})\n"
                f"**Reason:** {warn.reason or 'No reason provided'}\n"
                f"**Date:** {disnake.utils.format_dt(warn.date.timestamp(), style='f')}\n"
                f"**Removes at:** {disnake.utils.format_dt(warn.remove_at.timestamp(), style='f') if warn.remove_at else "Never"}"
            ),
        ).get_embed()
        for warn in warns
        for member in [await interaction.guild.get_or_fetch_member(warn.user.id)]
        for moderator in [await interaction.guild.get_or_fetch_member(warn.warned_by)]
    ]

    return warn_pages, None
