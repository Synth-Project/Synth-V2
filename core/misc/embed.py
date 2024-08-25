from typing import Any, Dict, List, Optional, Union

import disnake
import mafic
import math


def custom_embed(
    title: str = None,
    description: str = None,
    color: Union[disnake.Colour, int, None] = 0x2F3236,
    image: str = None,
    thumbnail: str = None,
) -> disnake.Embed:

    embed = disnake.Embed()
    embed.set_footer(text="Synth © 2024 | All Rights Reserved")

    embed.title = title
    embed.description = description
    embed.colour = color
    embed.set_image(url=image)
    embed.set_thumbnail(url=thumbnail)

    return embed


class EmbedPaginator(disnake.ui.View):
    def __init__(
        self,
        interaction: Union[
            disnake.MessageCommandInteraction, disnake.MessageInteraction
        ],
        author: disnake.Member,
        embed: disnake.Embed,
        data: Optional[Union[Dict, List]],
        timeout: Optional[int] = None,
        separate: int = 10,
    ) -> None:
        super().__init__(timeout=timeout)
        self.current_page = 1
        self.interaction = interaction
        self.author: disnake.Member = author
        self.embed: disnake.Embed = embed
        self.separate = separate
        self.data = data

    async def send_message(
        self,
        ctx: Union[
            disnake.ext.commands.Context,
            disnake.MessageCommandInteraction,
            disnake.MessageInteraction,
        ],
    ) -> Union[disnake.Message, Any]:
        self.prev_page.disabled = True
        self.next_page.disabled = False

        if isinstance(
            ctx, (disnake.MessageCommandInteraction, disnake.MessageInteraction)
        ):
            return await ctx.response.send_message(
                embed=self.embed, view=self, ephemeral=True
            )
        return await ctx.send(embed=self.embed, view=self)

    async def _create_embed(
        self, embed: disnake.Embed, data: Union[Dict, List]
    ) -> disnake.Embed:
        embed: disnake.Embed = disnake.Embed(
            title=embed.title,
            colour=embed.colour,
            timestamp=embed.timestamp,
            description="",
        )

        for index, music in enumerate(data, start=1):
            if index > self.separate:
                break

            music: mafic.Track
            embed.description += f"`{index}.` **{music.author} - {music.title}**\n"

        all_pages = math.ceil(len(self.data) / self.separate) - 1
        embed.set_footer(text=f"Page {self.current_page} of {all_pages}")

        return embed

    async def update(
        self,
        message: Union[disnake.MessageCommandInteraction, disnake.MessageInteraction],
        embed: disnake.Embed,
    ) -> None:
        await message.edit_original_response(embed=embed, view=self)

    @disnake.ui.button(label="️◀️", style=disnake.ButtonStyle.blurple)
    async def prev_page(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        if self.current_page <= 0:
            self.prev_page.disabled = True
            self.next_page.disabled = False

            return await self.update(self.interaction, self.embed)

        await interaction.response.defer()

        self.current_page -= 1

        if self.current_page <= 0:
            self.prev_page.disabled = True
            self.next_page.disabled = False
            return await self.update(self.interaction, self.embed)
        else:
            self.prev_page.disabled = False if self.current_page > 0 else True
            self.next_page.disabled = (
                False
                if self.current_page < (math.ceil(len(self.data) / self.separate) - 1)
                else True
            )

            start = self.current_page * self.separate
            data = self.data[start:]
            return await self.update(
                self.interaction, await self._create_embed(self.embed, data)
            )
        # await self.update_buttons()

    @disnake.ui.button(label="▶️", style=disnake.ButtonStyle.blurple)
    async def next_page(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        if self.current_page >= (math.ceil(len(self.data) / self.separate) - 1):
            self.next_page.disabled = True
            self.prev_page.disabled = False

            return await self.update(self.interaction, self.embed)

        await interaction.response.defer()
        self.current_page += 1

        self.prev_page.disabled = False if self.current_page > 0 else True
        self.next_page.disabled = (
            False
            if self.current_page < (math.ceil(len(self.data) / self.separate) - 1)
            else True
        )
        start = self.current_page * self.separate
        data = self.data[start:]
        return await self.update(
            self.interaction, await self._create_embed(self.embed, data)
        )
        # await self.update_buttons()

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.send(
                content="You are not allowed to use this buttons!", ephemeral=True
            )
            return False
        return True
