from typing import cast, Union
import importlib

import disnake
import wavelink
from disnake.ext import commands

from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed
from core.misc.music.views.navigation import NavigationDropdown
from core.misc.music.views.queue import QueueDropdown


class NavigationPanel(disnake.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
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

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

        if not player or not player._connected:
            embed = CustomEmbed(
                title="A misunderstanding happened",
                description=f"<:crossmark:1282338837456224394> I am not connected to a voice channel.",
            ).get_embed()
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if (
            not interaction.author.voice
            or interaction.author.voice.channel != player.channel
        ):
            embed = CustomEmbed(
                title="A misunderstanding happened",
                description=f"<:crossmark:1282338837456224394> You must be in the same voice channel as me!",
            ).get_embed()
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if not hasattr(player, "previous_votes"):
            player.previous_votes: set[int] = set()  # type: ignore

        user_id = interaction.author.id
        voice_channel = player.channel

        members_in_vc = [member for member in voice_channel.members if not member.bot]
        required_votes = len(members_in_vc) // 2 + len(members_in_vc) % 2

        if user_id in player.previous_votes:
            embed = CustomEmbed(
                title=f"<a:success:1168599845192339577> | Vote removed",
                description=f"({len(player.previous_votes)}/{required_votes}) to switch to the previous track",
                author=interaction.author,
            ).get_embed()
            player.previous_votes.remove(user_id)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        player.previous_votes.add(user_id)
        current_votes = len(player.previous_votes)

        if current_votes >= required_votes:
            skipped_track = player.current if player.playing else self.queue_.history.get()  # type: ignore
            previous_track = self.queue_.history.get()  # type: ignore
            self.queue_.put_at(0, previous_track)
            self.queue_.put_at(1, skipped_track)  # type: ignore
            if not player.playing:
                await player.play(self.queue_.get(), add_history=False)
            else:
                await player.skip()
            player.previous_votes.clear()
            return await interaction.response.defer(ephemeral=True)
        else:
            embed = CustomEmbed(
                title=f"<a:success:1168599845192339577> | Vote added",
                description=f"({current_votes}/{required_votes}) to switch to the previous track",
                author=interaction.author,
                # color=BasicColors.SUCCESS,
            ).get_embed()
            return await interaction.response.send_message(embed=embed, ephemeral=True)

    @disnake.ui.button(label=">", style=disnake.ButtonStyle.green, row=0, disabled=True)
    async def skip(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

        if not player or not player._connected:
            embed = CustomEmbed(
                title="A misunderstanding happened",
                description=f"<:crossmark:1282338837456224394> I am not connected to a voice channel.",
            ).get_embed()
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if (
            not interaction.author.voice
            or interaction.author.voice.channel != player.channel
        ):
            embed = CustomEmbed(
                title="A misunderstanding happened",
                description=f"<:crossmark:1282338837456224394> You must be in the same voice channel as me!",
            ).get_embed()
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if not hasattr(player, "skip_votes"):
            player.skip_votes: set[int] = set()  # type: ignore

        user_id = interaction.author.id
        voice_channel = player.channel

        members_in_vc = [member for member in voice_channel.members if not member.bot]
        required_votes = len(members_in_vc) // 2 + len(members_in_vc) % 2

        if user_id in player.skip_votes:
            embed = CustomEmbed(
                title=f"<a:success:1168599845192339577> | Vote removed",
                description=f"({len(player.skip_votes)}/{required_votes}) to skip the current track",
                author=interaction.author,
                # color=BasicColors.SUCCESS,
            ).get_embed()
            player.skip_votes.remove(user_id)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        player.skip_votes.add(user_id)

        current_votes = len(player.skip_votes)

        if current_votes >= required_votes:
            if player.current:
                if (
                    self.queue_.history.count == 0  # type: ignore
                    or player.current != self.queue_.history[0]  # type: ignore
                ):
                    self.queue_.history.put_at(0, player.current)  # type: ignore
            await player.skip()
            player.skip_votes.clear()
            return await interaction.response.defer(ephemeral=True)
        else:
            embed = CustomEmbed(
                title=f"<a:success:1168599845192339577> | Vote added",
                description=f"({current_votes}/{required_votes}) to skip the current track",
                author=interaction.author,
                # color=BasicColors.SUCCESS,
            ).get_embed()
            return await interaction.response.send_message(embed=embed, ephemeral=True)

    @disnake.ui.button(label="Pause/Resume", style=disnake.ButtonStyle.gray, row=0)
    async def resume_and_pause(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        await player.pause(not player.paused)
        self.resume_and_pause.label = "Resume" if player.paused else "Pause"

        if player.paused:
            for item in self.children:
                if item != self.resume_and_pause:
                    item.disabled = True  # type: ignore

            await interaction.response.edit_message(view=self)
        else:
            for item in self.children:
                item.disabled = False  # type: ignore

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
        functions = getattr(
            importlib.import_module("core.misc.music.functions"), "MusicFunctions"
        )
        await functions.display_queue(interaction)

    @disnake.ui.button(label="Autoplay", style=disnake.ButtonStyle.green, row=1)
    async def autoplay(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

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
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

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
        voice_channel_id = interaction.guild.voice_client.channel.id  # type: ignore
        voice_channel = interaction.guild.get_channel_or_thread(  # type: ignore
            voice_channel_id
        ) or await interaction.guild.fetch_channel(
            voice_channel_id
        )  # type: ignore

        if not (
            interaction.author.voice  # type: ignore
            and interaction.author.voice.channel.id == voice_channel.id  # type: ignore
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
