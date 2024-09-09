from typing import Optional, cast

import disnake
import wavelink
from disnake.ext import commands

from core.misc.color import BasicColors
from core.misc.embed import custom_embed


class ShuffleView(disnake.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        original_queue: wavelink.Queue,
        original_auto_queue: wavelink.Queue,
    ):
        super().__init__(timeout=180)

        self.bot = bot
        self.interaction = interaction
        self.queue = original_queue
        self.auto_queue = original_auto_queue
        self.original_queue = self.queue if not self.queue.is_empty else self.auto_queue

    def get_next_song(self, player: wavelink.Player) -> Optional[wavelink.Playable]:
        """
        Helper function to get the next song in the queue.

        Parameters:
        player (wavelink.Player): The player to get the next song from.

        Returns:
        Optional[wavelink.Playable]: The next song in the queue or None if the queue is empty.
        """
        return (
            player.queue[0]
            if not player.queue.is_empty
            else player.auto_queue[0] if not player.auto_queue.is_empty else None
        )

    async def send_response(
        self,
        interaction: disnake.MessageInteraction,
        embed: disnake.Embed,
        view: Optional[disnake.ui.View] = None,
    ):
        """
        Helper function to send the response to the interaction.

        Parameters:
        interaction (disnake.MessageInteraction): The interaction to send the response to.
        embed (disnake.Embed): The embed to send.
        view (Optional[disnake.ui.View], optional): The view to send. Defaults to None.

        Returns: None
        """
        await interaction.response.defer()
        await interaction.edit_original_response(embed=embed, view=view)

    @disnake.ui.button(label="Re-shuffle", style=disnake.ButtonStyle.green)
    async def shuffle(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if player.queue.is_empty and player.auto_queue.is_empty:
            embed = custom_embed(
                title="<:crossmark:1282338837456224394> There are no songs in the queue yet",
                color=BasicColors.ERROR,
            )
            return await self.send_response(interaction, embed, view=None)

        (player.auto_queue if player.queue.is_empty else player.queue).shuffle()

        track = player.current
        next_song = self.get_next_song(player)
        embed = custom_embed(
            title="<:shuffle:1279835431315308605>  Shuffled the queue",
            description=f"Current song: **{track.title}**\nNext song: **{next_song.title if next_song else 'None'}**",
            color=BasicColors.SUCCESS,
        )
        await self.send_response(interaction, embed)

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.red)
    async def cancel(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        """
        Cancel the shuffle

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to

        Returns: None
        """
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        await interaction.response.defer()
        if not hasattr(player, "previous_queue") or not hasattr(
            player, "previous_auto_queue"
        ):
            embed = custom_embed(
                title="There are no songs in the queue yet", color=BasicColors.ERROR
            )
            return await interaction.edit_original_response(embed=embed)

        if not player.queue.is_empty:
            player.queue = self.original_queue.copy()

        if (
            not player.auto_queue.is_empty
            and player.autoplay == wavelink.AutoPlayMode.enabled
        ):
            player.auto_queue = self.original_queue.copy()

        track = player.current
        next_song = self.get_next_song(player)

        embed = custom_embed(
            title="Queue restored to original",
            description=f"Current song: **{track.title}**\nNext song: **{next_song.title if next_song else 'None'}**",
        )
        await self.send_response(interaction, embed, view=None)

    # TODO: Cancel and Re-Shuffle should not be even available if no queue found and autoplay is disabled, so we need to delete the " if not hasattr(player, "previous_queue") or not hasattr(player, "previous_auto_queue"):"
