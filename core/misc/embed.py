import disnake

from typing import Union
from core.main.main import bot
from core.misc.color import BasicColors


def custom_embed(
    title: str = None,
    description: str = "",
    color: Union[disnake.Colour, int, BasicColors, None] = BasicColors.DEFAULT,
    image: str = None,
    thumbnail: str = None,
    footer: str = "Synth 2024 | All Rights Reserved",
    author: Union[disnake.Member, disnake.User] = None,
) -> disnake.Embed:
    """
    creates a custom embed.

    Args:
        title (str, optional): The title of the embed. defaults to None.
        description (str, optional): The description of the embed. defaults to "".
        color (Union[disnake.Colour, int, BasicColors, None], optional): The color of the embed. defaults to 0x2F3236.
        image (str, optional): The URL of the image in the embed. defaults to None.
        thumbnail (str, optional): The URL of the thumbnail in the embed. defaults to None.
        footer (str, optional): The footer of the embed. defaults to "Synth 2024 | All Rights Reserved".
        author (Union[disnake.Member, disnake.User], optional): The author of the embed. defaults to None.

    Returns:
        disnake.Embed: The custom embed.
    """
    if isinstance(color, BasicColors):
        color = color.value
    embed = disnake.Embed()
    embed.set_footer(text=footer, icon_url=bot.Bot().get_avatar())

    if author:
        embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)

    embed.title = title
    embed.description = description
    embed.colour = color
    embed.set_image(url=image)
    embed.set_thumbnail(url=thumbnail)

    return embed
