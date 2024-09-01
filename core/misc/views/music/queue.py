from datetime import timedelta

import disnake
from disnake.ext import commands
import wavelink


class QueueDropdown(disnake.ui.Select):
    def __init__(self, bot: commands.Bot, player: wavelink.Player) -> None:
        self.bot = bot

        self.player = player
        self.queue = (
            player.queue
            if not player.queue.is_empty and player.queue.count >= 1
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else []
            )
        )

        self.items_per_page = 23
        self.page = 1
        self.emojis = (["<:youtube:1279826494847451199>"] * ((len(self.queue) // 2) + 1))[:len(self.queue)]

        super().__init__(
            placeholder="Skip to a track",
            min_values=1,
            max_values=1,
            options=self._get_options(),
        )

    def _get_options(self):
        start_idx = (self.page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page

        options = []

        if self.page > 1:
            options.append(
                disnake.SelectOption(emoji="◀️", label="Previous", value="previous")
            )

        options.extend(
            disnake.SelectOption(
                emoji=self.emojis[index],
                label=track.title,
                value=str(index),
                description=f"{str(timedelta(seconds=round(track.length / 1000)))}",
            )
            for index, track in enumerate(
                self.queue[start_idx:end_idx], start=start_idx
            )
        )

        if end_idx < len(self.queue):
            options.append(disnake.SelectOption(emoji="▶️", label="Next", value="next"))

        return options

    async def callback(self, interaction: disnake.MessageInteraction):
        match self.values[0]:
            case "next":
                self.page += 1
                self.options = self._get_options()
                await interaction.response.edit_message(view=self.view)

            case "previous":
                self.page -= 1
                self.options = self._get_options()
                await interaction.response.edit_message(view=self.view)

            case _:
                track_index = int(self.values[0])
                track = self.queue[track_index]
                await interaction.response.send_message(
                    f"You have skipped: {track.title}", ephemeral=True
                )

                self.player.queue.put_at(0, track)
                self.player.queue.put_at(1, self.player.current)
                self.player.queue.history.put_at(0, self.player.current)

                await self.player.skip()
