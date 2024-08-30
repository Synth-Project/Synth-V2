import disnake
from disnake.ext import commands

import wavelink

from core.misc.embed import custom_embed, CreatePaginator


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
                label=track.title,
                value=str(index),
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


class NavigationDropdown(disnake.ui.Select):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(
            placeholder="Music controls",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(
                    label="Volume",
                    value="volume",
                ),
                disnake.SelectOption(
                    label="Shuffle",
                    value="shuffle",
                ),
                disnake.SelectOption(
                    label="Disconnect",
                    value="disconnect",
                ),
            ],
        )
        self.bot = bot

    async def volume_change(self, interaction: disnake.MessageInteraction) -> None:
        player: wavelink.Player = interaction.guild.voice_client

        modal = disnake.ui.Modal(
            title="Enter the volume",
            custom_id="volume",
            components=[
                disnake.ui.TextInput(
                    label="New volume:",
                    custom_id="new_volume",
                    style=disnake.TextInputStyle.short,
                )
            ],
        )
        await interaction.response.send_modal(modal=modal)
        response_modal: disnake.ModalInteraction = await self.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == "volume" and i.user == interaction.user,
        )
        new_volume = int(response_modal.text_values.get("new_volume", 0))

        if new_volume > 100 or new_volume < 1:
            error_embed = custom_embed(color=disnake.Color.red())
            error_embed.title = f"Please enter a number, between `1` and `100`"
            return await response_modal.response.send_message(
                embed=error_embed, ephemeral=True
            )

        await player.set_volume(new_volume)
        await response_modal.response.send_message(
            embed=custom_embed(title=f"Set volume to {new_volume}"),
            ephemeral=True,
        )

    async def callback(self, interaction: disnake.Interaction) -> None:
        selected_option = self.values[0]
        player: wavelink.Player = interaction.guild.voice_client

        match selected_option:
            case "volume":
                await self.volume_change(interaction)
            case "shuffle":
                if player.queue.is_empty and player.auto_queue.is_empty:
                    embed = custom_embed(
                        title="There are no songs in the queue yet",
                        color=disnake.Color.red(),
                    )
                    return await interaction.response.send_message(
                        embed=embed, ephemeral=True
                    )
                elif player.queue.is_empty and not player.auto_queue.is_empty:
                    player.auto_queue.shuffle()
                else:
                    player.queue.shuffle()

                track: wavelink.Track = player.current
                next_song = (
                    player.queue[0]
                    if not player.queue.is_empty
                    else player.auto_queue[0]
                )

                embed = custom_embed(
                    title="Shuffled the queue",
                    description=f"Current song: **{track.title}**\nNext song: **{next_song.title}**",
                    color=disnake.Colour.green(),
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

            case "disconnect":
                await player.disconnect()

                embed = custom_embed(
                    title=f"Disconnected from voice channel",
                    color=disnake.Colour.red(),
                )
                await interaction.response.edit_message(embed=embed, view=None)


class NavigationPanel(disnake.ui.View):
    def __init__(
        self,
        bot: commands.bot,
        message_id: int,
        player: wavelink.Player,
        history_exists: bool = False,
        *,
        timeout: float | None = None,
    ) -> None:

        super().__init__(timeout=timeout)

        self.message_id = message_id
        self.bot = bot
        self.queue_ = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )

        self.add_item(NavigationDropdown(bot=self.bot))

        if player.queue.count >= 1 or (
            player.auto_queue
            and player.auto_queue.count >= 1
            and player.autoplay == wavelink.AutoPlayMode.enabled
        ):
            self.add_item(QueueDropdown(bot=self.bot, player=player))

        self.previous.disabled = not history_exists
        self.skip.disabled = not len(self.queue_) >= 1
        self.autoplay.style = (
            disnake.ButtonStyle.green
            if player.autoplay == wavelink.AutoPlayMode.enabled
            else disnake.ButtonStyle.red
        )

    @disnake.ui.button(label="<", style=disnake.ButtonStyle.green, row=0, disabled=True)
    async def previous(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = interaction.guild.voice_client

        previous_track = player.queue.history.get()
        self.queue_.put_at(0, previous_track)

        skipped_track = await player.skip()
        self.queue_.put_at(1, skipped_track)

        await interaction.response.defer(ephemeral=True)

    @disnake.ui.button(label=">", style=disnake.ButtonStyle.green, row=0, disabled=True)
    async def skip(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = interaction.guild.voice_client

        try:
            self.queue_.history.put_at(0, player.current)

            await player.skip()

            message = await interaction.channel.fetch_message(self.message_id)
            await message.delete()

            await interaction.response.defer(ephemeral=True)

        except (
            wavelink.InvalidClientException,
            wavelink.InvalidNodeException,
            disnake.Forbidden,
            disnake.NotFound,
        ):
            pass

    @disnake.ui.button(label="Pause/Resume", style=disnake.ButtonStyle.gray, row=0)
    async def resume_and_pause(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = interaction.guild.voice_client

        if player.paused:
            await player.pause(False)
            await interaction.response.edit_message(content=f"")
        else:
            await player.pause(True)
            await interaction.response.edit_message(content=f"")

    @disnake.ui.button(label="Queue", style=disnake.ButtonStyle.blurple, row=1)
    async def queue(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = interaction.guild.voice_client

        if not player.queue:
            embed = disnake.Embed(
                title="Music Queue", description="No music in the queue"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        queue_list = list(enumerate(player.queue, start=1))

        embeds = [
            disnake.Embed(
                title="Music Queue",
                description="\n".join(
                    f"`{index}.` **{music.author} - {music.title}**"
                    for index, music in queue_list[i : i + 10]
                ),
                color=0x2F3236,
            )
            for i in range(0, len(queue_list), 10)
        ]

        paginator = CreatePaginator(embeds=embeds, author_id=interaction.author.id)
        await interaction.response.send_message(
            embed=embeds[0], view=paginator, ephemeral=True
        )

    @disnake.ui.button(label="Autoplay", style=disnake.ButtonStyle.green, row=1)
    async def autoplay(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = interaction.guild.voice_client

        if player:
            if player.autoplay == wavelink.AutoPlayMode.enabled:
                player.autoplay = wavelink.AutoPlayMode.disabled
                self.autoplay.style = disnake.ButtonStyle.red
                await interaction.response.edit_message(
                    content="Autoplay disabled", view=self
                )
            else:
                player.autoplay = wavelink.AutoPlayMode.enabled
                self.autoplay.style = disnake.ButtonStyle.green
                await interaction.response.edit_message(
                    content="Autoplay enabled", view=self
                )

    @disnake.ui.button(label="Loop", style=disnake.ButtonStyle.green, row=1)
    async def loop(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer(ephemeral=True)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        # return await super().interaction_check(interaction)
        voice_channel = interaction.guild.get_channel_or_thread(
            interaction.guild.voice_client.channel.id
        ) or await interaction.guild.fetch_channel(
            interaction.guild.voice_client.channel.id
        )

        if interaction.author.voice.channel.id == voice_channel.id:
            return True
        else:
            await interaction.response.send_message(
                f":x: You must be in a {voice_channel.mention} to use this command",
                ephemeral=True,
            )
            return False
