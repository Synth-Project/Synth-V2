import disnake

from typing import Union


def custom_embed(
    title: str = None,
    description: str = "",
    color: Union[disnake.Colour, int, None] = 0x2F3236,
    image: str = None,
    thumbnail: str = None,
) -> disnake.Embed:
    """
    Create a custom embed.
    :param title: The title of the embed.
    :param description: The description of the embed.
    :param color: The color of the embed.
    :param image: The image of the embed.
    :param thumbnail: The thumbnail of the embed.
    :return: The created embed.
    """

    embed = disnake.Embed()
    embed.set_footer(text="Synth © 2024 | All Rights Reserved")

    embed.title = title
    embed.description = description
    embed.colour = color
    embed.set_image(url=image)
    embed.set_thumbnail(url=thumbnail)

    return embed
