from typing import cast

import disnake
import wavelink
from disnake.ext import commands

from core.misc.color import BasicColors
from core.misc.embed import custom_embed


class ShuffleView(disnake.ui.View):
    def __init__(
        self, bot: commands.Bot, interaction: disnake.Interaction, original_queue: wavelink.Queue,
        original_auto_queue: wavelink.Queue
    ):
        super().__init__(timeout=180)
        self.bot = bot
        self.interaction = interaction
        self.queue: wavelink.Queue = original_queue
        self.auto_queue: wavelink.Queue = original_auto_queue

        self.original_queue = self.queue if not self.queue.is_empty else self.auto_queue

    @disnake.ui.button(label="Re-shuffle", style=disnake.ButtonStyle.green)
    async def shuffle(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if player.queue.is_empty and player.auto_queue.is_empty:
            embed = custom_embed(
                title="There are no songs in the queue yet",
                color=BasicColors.ERROR,
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            await interaction.edit_original_response(view=None)
            return
        elif player.queue.is_empty and not player.auto_queue.is_empty:
            player.auto_queue.shuffle()
        else:
            player.queue.shuffle()

        track: wavelink.Playable = player.current
        next_song = (
            player.queue[0]
            if not player.queue.is_empty
            else player.auto_queue[0]
        )

        embed = custom_embed(
            title="Shuffled the queue",
            description=f"Current song: **{track.title}**\nNext song: **{next_song.title}**",
            color=BasicColors.SUCCESS,
        )

        await interaction.response.defer()
        await interaction.edit_original_response(embed=embed)

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.red)
    async def cancel(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        await interaction.response.defer()
        if not hasattr(player, "previous_queue") or not hasattr(player, "previous_auto_queue"):
            embed = custom_embed(
                title="There are no songs in the queue yet",
                color=BasicColors.ERROR,
            )
            return await interaction.edit_original_response(embed=embed)

        if not player.queue.is_empty:
            player.queue = self.original_queue.copy()

        if not player.auto_queue.is_empty and player.autoplay == wavelink.AutoPlayMode.enabled:
            player.auto_queue = self.original_queue.copy()

        track: wavelink.Playable = player.current
        next_song = (
            player.queue[0]
            if not player.queue.is_empty
            else player.auto_queue[0]
            if not player.auto_queue.is_empty
               and player.autoplay == wavelink.AutoPlayMode.enabled
            else "None"
        )

        embed = custom_embed(
            title="Queue restored to original",
            description=f"Current song: **{track.title}**\nNext song: **{next_song}**",
            color=BasicColors.SUCCESS,
        )

        await self.interaction.edit_original_response(view=self)
        return await interaction.edit_original_response(embed=embed, view=None)
