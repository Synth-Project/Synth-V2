from datetime import timedelta

import disnake
import wavelink
from disnake.ext import commands


class QueueDropdown(disnake.ui.Select):
    """
    Queue dropdown menu class for music player
    :disnake.ui.Select:
    """

    def __init__(self, bot: commands.Bot, player: wavelink.Player) -> None:
        self.bot = bot
        self.player = player
        self.queue = self._get_queue()
        self.items_per_page = 23
        self.page = 1

        self.options = self._get_options() or [
            disnake.SelectOption(
                emoji="<:crossmark:1282338837456224394>",
                label="Queue is empty",
                value="none",
            )
        ]
        super().__init__(
            placeholder="Skip to a track",
            min_values=1,
            max_values=1,
            options=self.options,
            disabled=not bool(self.queue),
        )

    def _get_queue(self) -> list:
        """
        Get the current queue
        :return: list
        """
        return (
            self.player.queue
            if not self.player.queue.is_empty and self.player.queue.count >= 1
            else (
                self.player.auto_queue
                if self.player.autoplay == wavelink.AutoPlayMode.enabled
                else []
            )
        )

    def _get_options(self):
        """
        Get the options for the dropdown menu
        :return: list
        """
        start_idx, end_idx = (
                                     self.page - 1
                             ) * self.items_per_page, self.page * self.items_per_page
        options = []

        if self.page > 1:
            options.append(
                disnake.SelectOption(emoji="◀️", label="Previous", value="previous")
            )

        track: wavelink.Playable
        for index, track in enumerate(self.queue[start_idx:end_idx], start=start_idx):
            requested_by = (
                self.bot.get_guild(self.player.guild.id).get_member(int(track.extras.requested_by)).name
                if hasattr(track.extras, "requested_by")
                else "Auto recommended"
            )

            options.append(
                disnake.SelectOption(
                    emoji="<:youtube:1279826494847451199>",
                    label=track.title,
                    value=str(index),
                    description=f"{timedelta(seconds=round(track.length / 1000))} // Requested by: {requested_by}",
                )
            )

        if end_idx < len(self.queue):
            options.append(disnake.SelectOption(emoji="▶️", label="Next", value="next"))

        return options

    async def callback(self, interaction: disnake.MessageInteraction):
        """
        Callback for the dropdown menu

        Parameters
        Interaction:
            disnake.MessageInteraction

        Return: None
        """
        selected_value = self.values[0]
        if selected_value == "next":
            self.page += 1
        elif selected_value == "previous":
            self.page -= 1
        else:
            track = self.queue[int(selected_value)]
            await interaction.response.send_message(
                f"Skipped to: {track.title}", ephemeral=True
            )
            self.player.queue.put_at(0, track)
            await self.player.skip()

        self.options = self._get_options()
        await interaction.response.edit_message(view=self.view)
