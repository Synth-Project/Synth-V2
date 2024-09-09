from typing import Union

import disnake

from core.main.main import bot
from core.misc.color import BasicColors


def custom_embed(
    title: str = None,
    description: str = "",
    color: Union[disnake.Colour, int, BasicColors, None] = BasicColors.DEFAULT,
    image: str = None,
    thumbnail: str = None,
    footer_text: str = "Synth 2024 // All rights reserved",
    author: Union[disnake.Member, disnake.User] = None,
) -> disnake.Embed:
    """
    creates a custom embed.

    Parameters:
        title (str, optional): The title of the embed. defaults to None.
        description (str, optional): The description of the embed. defaults to "".
        color (Union[disnake.Colour, int, BasicColors, None], optional): The color of the embed. defaults to 0x2F3236.
        image (str, optional): The URL of the image in the embed. defaults to None.
        thumbnail (str, optional): The URL of the thumbnail in the embed. defaults to None.
        footer_text (str, optional): The footer of the embed. defaults to "Synth 2024 | All Rights Reserved".
        author (Union[disnake.Member, disnake.User], optional): The author of the embed. defaults to None.

    Returns:
        disnake.Embed: The custom embed.
    """
    if isinstance(color, BasicColors):
        color = color.value
    embed = disnake.Embed()

    embed.set_footer(
        text=footer_text,
        icon_url=bot.get_avatar(),
    )

    if author:
        embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)

    embed.title = title
    embed.description = description
    embed.colour = color
    embed.set_image(url=image)
    embed.set_thumbnail(url=thumbnail)

    return embed


def error_embed(
    title: str = None,
    description: str = "",
    image: str = None,
    thumbnail: str = None,
    footer_text: str = "Synth 2024 // All rights reserved",
    author: Union[disnake.Member, disnake.User] = None,
):
    embed = custom_embed(
        title=title,
        description=description,
        color=BasicColors.ERROR,
        image=image,
        thumbnail=thumbnail,
        footer_text=footer_text,
        author=author,
    )

    return embed
