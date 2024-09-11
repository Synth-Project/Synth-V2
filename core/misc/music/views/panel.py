from datetime import timedelta
from typing import cast, Union

import disnake
import wavelink
from disnake.ext import commands

from core.misc.embed import CustomEmbed
from core.misc.music.views.navigation import NavigationDropdown
from core.misc.music.views.queue import QueueDropdown
from core.misc.paginator import CreatePaginator


class NavigationPanel(disnake.ui.View):
    def __init__(
        self,
        bot: commands.bot,
        message_id: int,
        player: wavelink.Player,
        history_exists: bool = False,
        *,
        timeout: float | None = None,
        interaction: Union[disnake.Interaction, disnake.WebhookMessage],
    ) -> None:

        super().__init__(timeout=timeout)

        self.bot = bot
        self.message_id = message_id
        self.interaction = interaction

        self.player: wavelink.Player = player
        self.history_exists: bool = history_exists
        self.queue_dropdown = QueueDropdown(bot=self.bot, player=self.player)
        self.navigation_dropdown = NavigationDropdown(
            bot=self.bot,
            interaction=self.interaction,
            player=self.player,
        )

        self.queue_ = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )

        self._setup_hooks()

    def _setup_hooks(self) -> None:
        self.add_item(self.navigation_dropdown)
        self.add_item(self.queue_dropdown)

        self.queue.disabled = self.player.paused or self.queue_.count < 1
        self.skip.disabled = self.player.paused or len(self.queue_) < 1
        self.previous.disabled = (
            self.player.paused
            or not self.history_exists
            or self.queue_.history.count < 1
        )
        self.queue_dropdown.disabled = self.player.paused or self.queue_.count < 1
        self.navigation_dropdown.disabled = self.player.paused

        self.autoplay.style = (
            disnake.ButtonStyle.green
            if self.player.autoplay == wavelink.AutoPlayMode.enabled
            else disnake.ButtonStyle.red
        )
        self.autoplay.disabled = self.player.paused

        self.loop.style = (
            disnake.ButtonStyle.green
            if self.queue_.mode == wavelink.QueueMode.loop
            else disnake.ButtonStyle.red
        )
        self.loop.disabled = self.player.paused

        self.resume_and_pause.label = "Resume" if self.player.paused else "Pause"

    @disnake.ui.button(label="<", style=disnake.ButtonStyle.green, row=0, disabled=True)
    async def previous(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        skipped_track = player.current if player.playing else self.queue_.history.get()
        previous_track = self.queue_.history.get()

        self.queue_.put_at(0, previous_track)
        self.queue_.put_at(1, skipped_track)

        if not player.playing:
            await player.play(self.queue_.get(), add_history=False)
        else:
            await player.skip()

        await interaction.response.defer(ephemeral=True)

    @disnake.ui.button(label=">", style=disnake.ButtonStyle.green, row=0, disabled=True)
    async def skip(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if player.current:
            if (
                self.queue_.history.count == 0
                or player.current != self.queue_.history[0]
            ):
                self.queue_.history.put_at(0, player.current)
        # self.queue_.history.put_at(0, player.current)
        print(self.queue_.history)
        await player.skip()

        await interaction.response.defer(ephemeral=True)

    @disnake.ui.button(label="Pause/Resume", style=disnake.ButtonStyle.gray, row=0)
    async def resume_and_pause(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        await player.pause(not player.paused)
        self.resume_and_pause.label = "Resume" if player.paused else "Pause"

        if player.paused:
            for item in self.children:
                if item != self.resume_and_pause:
                    item.disabled = True

            await interaction.response.edit_message(view=self)
        else:
            for item in self.children:
                item.disabled = False

            self.queue.disabled = self.player.paused or self.queue_.count < 1
            self.skip.disabled = self.player.paused or len(self.queue_) < 1
            self.previous.disabled = self.player.paused or not self.history_exists
            self.queue_dropdown.disabled = self.queue_.count < 1

            await interaction.response.edit_message(view=self)

    @disnake.ui.button(
        label="Queue", style=disnake.ButtonStyle.blurple, row=1, disabled=True
    )
    async def queue(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        queue_list = list(enumerate(self.queue_, start=1))

        embeds = [
            CustomEmbed(
                title=f"{interaction.guild.name}'s Queue",
                description="\n".join(
                    [
                        f"`[ {str(timedelta(seconds=round(music.length / 1000)))} ]` {music.title} // Requested by: "
                        f"{(await self.bot.get_or_fetch_user(music.extras.requested_by)).name if music.extras.requested_by else 'Unknown'}"
                        for _, music in queue_list[i : i + 10]
                        if music
                    ]
                ),
            ).get_embed()
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
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        assert player

        if player.autoplay == wavelink.AutoPlayMode.enabled:
            player.autoplay = wavelink.AutoPlayMode.disabled
            self.autoplay.style = disnake.ButtonStyle.red

        else:
            player.autoplay = wavelink.AutoPlayMode.enabled
            self.queue_.mode = wavelink.QueueMode.normal

            self.autoplay.style = disnake.ButtonStyle.green
            self.loop.style = disnake.ButtonStyle.red

        await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Loop", style=disnake.ButtonStyle.green, row=1)
    async def loop(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        assert player

        if self.queue_.mode == wavelink.QueueMode.normal:
            player.autoplay = wavelink.AutoPlayMode.disabled
            self.queue_.mode = wavelink.QueueMode.loop

            self.loop.style = disnake.ButtonStyle.green
            self.autoplay.style = disnake.ButtonStyle.red
        else:
            self.queue_.mode = wavelink.QueueMode.normal
            self.loop.style = disnake.ButtonStyle.red

        await interaction.response.edit_message(view=self)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        voice_channel_id = interaction.guild.voice_client.channel.id
        voice_channel = interaction.guild.get_channel_or_thread(
            voice_channel_id
        ) or await interaction.guild.fetch_channel(voice_channel_id)

        if not (
            interaction.author.voice
            and interaction.author.voice.channel.id == voice_channel.id
        ):
            embed = CustomEmbed(
                title="A misunderstanding happened",
                description=f"<:crossmark:1282338837456224394> You must be in {voice_channel.mention} to use this command",
            ).get_embed()
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            if isinstance(self.interaction, disnake.Interaction):
                await self.interaction.edit_original_response(view=self)
            elif isinstance(self.interaction, disnake.WebhookMessage):
                await self.interaction.edit(view=self)

            return False

        return True
