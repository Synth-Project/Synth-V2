from typing import Union, Literal

import disnake
from disnake import Embed

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


class CustomEmbed:
    def __init__(
        self,
        embed_type: Literal["default", "error"] = "default",
        title: str = "",
        description: str = "",
        color: Union[disnake.Colour, int, BasicColors] = BasicColors.DEFAULT,
        image: str = None,
        thumbnail: str = None,
        footer_text: str = "Synth 2024 // All rights reserved",
        author: Union[disnake.Member, disnake.User] = None,
    ):
        self._embed = self._build_embed(
            title, description, color, image, thumbnail, footer_text, author
        )
        if embed_type == "error":
            self._embed.colour = BasicColors.ERROR.value

    @staticmethod
    def _build_embed(
        title: str,
        description: str,
        color: Union[disnake.Colour, int, BasicColors],
        image: str,
        thumbnail: str,
        footer_text: str,
        author: Union[disnake.Member, disnake.User],
    ) -> disnake.Embed:
        """Build a common embed structure."""
        if isinstance(color, BasicColors):
            color = color.value

        embed = disnake.Embed(title=title, description=description, color=color)
        embed.set_footer(text=footer_text, icon_url=bot.get_avatar())

        if author:
            embed.set_author(
                name=author.display_name, icon_url=author.display_avatar.url
            )

        if image:
            embed.set_image(url=image)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        return embed

    def get_embed(self) -> disnake.Embed:
        """Retrieve the constructed embed."""
        return self._embed

    def to_dict(self) -> dict:
        return self.get_embed().to_dict()

    @classmethod
    async def from_json(cls, json: dict) -> Embed:
        """Create a CustomEmbed from a JSON object."""
        return cls()._embed.from_dict(json)

    @classmethod
    def error_embed(
        cls, title: str = None,
        description: str = "",
        image: str = None,
        thumbnail: str = None,
        footer_text: str = "Synth 2024 // All rights reserved",
        author: Union[disnake.Member, disnake.User] = None,
    ):
        return cls(
            embed_type="error",
            title=title,
            description=description,
            image=image,
            thumbnail=thumbnail,
            footer_text=footer_text,
            author=author,
        )
