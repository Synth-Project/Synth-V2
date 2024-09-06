from typing import cast

import disnake
from disnake.ext import commands
import wavelink

from core.misc.paginator import CreatePaginator
from core.misc.embed import custom_embed
from core.misc.views.music.navigation import NavigationDropdown
from core.misc.views.music.queue import QueueDropdown


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

        self.bot = bot
        self.message_id = message_id

        self.player = player
        self.history_exists = history_exists

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

        self._setup_hooks()

    def _setup_hooks(self) -> None:
        if self.queue_.count >= 1:
            self.add_item(QueueDropdown(bot=self.bot, player=self.player))

        self.queue.disabled = self.player.paused or self.queue_.count < 1
        self.skip.disabled = self.player.paused or len(self.queue_) < 1
        self.previous.disabled = self.player.paused or not self.history_exists

        self.autoplay.style = (
            disnake.ButtonStyle.green
            if self.player.autoplay == wavelink.AutoPlayMode.enabled
            else disnake.ButtonStyle.red
        )
        self.loop.style = (
            disnake.ButtonStyle.green
            if self.queue_.mode == wavelink.QueueMode.loop
            else disnake.ButtonStyle.red
        )
        self.resume_and_pause.label = "Resume" if self.player.paused else "Pause"

    def _check_items(self, whitelist: list[str]) -> None:
        for item in self.children:
            if isinstance(item, disnake.ui.Button):
                if item.label not in whitelist:
                    item.disabled = self.player.paused

            elif isinstance(item, disnake.ui.Select):
                if item.placeholder not in whitelist:
                    item.disabled = self.player.paused

        self.queue.disabled = self.player.paused or self.queue_.count < 1
        self.skip.disabled = self.player.paused or len(self.queue_) < 1
        self.previous.disabled = self.player.paused or not self.history_exists

    @disnake.ui.button(label="<", style=disnake.ButtonStyle.green, row=0, disabled=True)
    async def previous(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        previous_track = player.queue.history.get()
        self.queue_.put_at(0, previous_track)

        skipped_track = await player.skip()
        self.queue_.put_at(1, skipped_track)

        await interaction.response.defer(ephemeral=True)

    @disnake.ui.button(label=">", style=disnake.ButtonStyle.green, row=0, disabled=True)
    async def skip(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

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

    @disnake.ui.button(style=disnake.ButtonStyle.gray, row=0)
    async def resume_and_pause(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        await player.pause(not player.paused)
        self.resume_and_pause.label = "Resume" if player.paused else "Pause"
        self.player = player

        self._check_items(["Pause", "Resume"])

        await interaction.response.edit_message(view=self)

    @disnake.ui.button(
        label="Queue", style=disnake.ButtonStyle.blurple, row=1, disabled=True
    )
    async def queue(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        queue_list = list(enumerate(self.queue_, start=1))

        embeds = [
            custom_embed(
                title="Music Queue",
                description="\n".join(
                    f"`{index}.` `{music.author}` - {music.title}"
                    for index, music in queue_list[i: i + 10]
                ),
                image="https://github.com/user-attachments/assets/571bb335-1cae-40e5-a5b5-0defe6ba1417",
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
        voice_channel = interaction.guild.get_channel_or_thread(
            interaction.guild.voice_client.channel.id
        ) or await interaction.guild.fetch_channel(
            interaction.guild.voice_client.channel.id
        )

        if (
                not interaction.author.voice
                or not interaction.author.voice.channel.id == voice_channel.id
        ):
            await interaction.response.send_message(
                f"❌ | You must be in a {voice_channel.mention} to use this command",
                ephemeral=True,
            )
            return False

        return True
