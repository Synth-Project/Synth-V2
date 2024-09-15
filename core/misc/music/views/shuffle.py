from typing import Optional, cast
import importlib

import disnake
import wavelink
from disnake.ext import commands

from core.misc.embed import CustomEmbed


class ShuffleView(disnake.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        original_queue: wavelink.Queue,
        original_auto_queue: wavelink.Queue,
    ) -> None:
        super().__init__(timeout=180)

        self.bot = bot
        self.interaction = interaction
        self.queue = original_queue
        self.auto_queue = original_auto_queue
        self.original_queue = self.queue if not self.queue.is_empty else self.auto_queue

        self.cancel.disabled = True if self.original_queue.is_empty else False

        self.functions = getattr(
            importlib.import_module("core.misc.music.functions"), "MusicFunctions"
        )

    @staticmethod
    def get_next_song(player: wavelink.Player) -> Optional[wavelink.Playable]:
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

    @staticmethod
    async def send_response(
        interaction: disnake.MessageInteraction,
        embed: disnake.Embed,
        view: Optional[disnake.ui.View] = None,
    ):
        """
        Helper function to send the response to the interaction.

        Parameters:
        interaction (disnake.MessageInteraction): The interaction to send the response to.
        Embed (disnake.Embed): The embed to send.
        View (Optional[disnake.ui.View], optional): The view to send. Defaults to None.

        Returns: None
        """
        await interaction.response.defer()
        await interaction.edit_original_response(embed=embed, view=view)

    @disnake.ui.button(label="Reshuffle", style=disnake.ButtonStyle.green)
    async def shuffle(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        """
        Re-shuffle the queue

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to

        Returns: None
        """
        self.shuffle.disabled = False
        await self.functions.shuffle_queue(interaction)

    @disnake.ui.button(label="Queue", style=disnake.ButtonStyle.blurple)
    async def queue(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        await self.functions.display_queue(interaction)

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

        if not player.queue.is_empty:
            player.queue = self.original_queue.copy()

        if (
            not player.auto_queue.is_empty
            and player.autoplay == wavelink.AutoPlayMode.enabled
        ):
            player.auto_queue = self.original_queue.copy()

        track = player.current
        next_song = self.get_next_song(player)

        embed = CustomEmbed(
            author=interaction.user,
            title="Queue restored to original",
            description=f"Current song: **{track.title}**\nNext song: **{next_song.title if next_song else 'None'}**",
        ).get_embed()
        await self.send_response(interaction, embed, view=None)
