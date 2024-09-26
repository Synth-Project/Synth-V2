import disnake
from disnake.ext import commands


def generate_time_options(input_text):
    units = {"с": "seconds", "м": "minutes", "h": "hours", "d": "days"}

    options = []
    for unit, unit_name in units.items():
        if input_text.endswith(unit):
            try:
                number = int(input_text[:-1])
                if number > 0:
                    options.append(
                        disnake.OptionChoice(
                            name=f"{number} {unit_name}",
                            value=str(
                                number * {"с": 1, "м": 60, "h": 3600, "d": 86400}[unit]
                            ),
                        )
                    )
            except ValueError:
                continue
    return options


def shorten_text(text: str, max_length: int = 75) -> str:
    """
    Shorten a given text to a certain length.

    If the text is longer than the given length, it will be shortened
    to the given length and "..." will be appended to the end.

    Parameters:
    text (str): The text to shorten.
    max_length (int): The maximum length of the text.

    Returns:
    str: The shortened text.
    """
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


async def get_channel(bot: commands.Bot, channel_id: int | str) -> disnake.abc.GuildChannel | bool:
    """Fetch a channel and return whether it was successful."""
    
    if isinstance(channel_id, str) and channel_id.isdigit():
        channel_id = int(channel_id)
    else:
        return False
    
    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(
            channel_id
        )
        return channel
    except (
        disnake.HTTPException,
        disnake.NotFound,
        disnake.Forbidden,
        disnake.InvalidData,
    ):
        return False