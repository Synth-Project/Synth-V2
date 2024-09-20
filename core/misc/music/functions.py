from typing import cast, Union
from dataclasses import dataclass
from datetime import timedelta

import disnake
from disnake.ext.commands import Bot
import wavelink

from core.main.main import bot

from core.misc.paginator import CreatePaginator
from core.misc.embed import CustomEmbed
from core.misc.color import BasicColors
from core.misc.music.errors import MusicError

from core.misc.music.views.panel import NavigationPanel
from core.misc.music.views.shuffle import ShuffleView


@dataclass
class MusicFunctions:
    @staticmethod
    async def music_embed(
        interaction: Union[disnake.ApplicationCommandInteraction, disnake.Message],
        track: wavelink.Playable,
    ) -> disnake.Embed:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        track = track or player.current

        requested = (
            await interaction.guild.get_or_fetch_member(int(track.extras.requested_by))
            if track.extras.requested_by
            else None
        )

        embed = CustomEmbed(
            author=requested, title="Now playing", image=track.artwork
        ).get_embed()
        embed.url = str(track.uri)

        embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
        embed.add_field(
            name="Duration:",
            value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
            inline=True,
        )

        footer = f"{'Paused //' if player.paused else ''} Volume: {player.volume}% // "
        if track.recommended:
            footer += "Auto recommended // "
        elif player.queue.mode == wavelink.QueueMode.loop:
            footer += "This track was looped // "

        footer += "Synth Music 2024"

        embed.set_footer(text=footer, icon_url=bot.get_avatar())

        return embed

    @staticmethod
    async def nowplaying(
        interaction: disnake.ApplicationCommandInteraction,
        track: wavelink.Playable = None,
    ) -> disnake.Embed:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        track = track or player.current

        requested = (
            await interaction.guild.get_or_fetch_member(int(track.extras.requested_by))
            if track.extras.requested_by
            else None
        )

        embed = CustomEmbed(
            author=requested, title="Now playing", image=track.artwork
        ).get_embed()
        embed.url = str(track.uri)

        embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
        embed.add_field(
            name="Duration:",
            value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
            inline=True,
        )
        embed.add_field(name="Album:", value=f"`{track.album.name}`", inline=True)
        embed.add_field(name="Requested by:", value=requested.mention, inline=True)

        footer = f"Volume: {player.volume}% // "
        if track.recommended:
            footer += "Auto recommended // "
        elif player.queue.mode == wavelink.QueueMode.loop:
            footer += "This track was looped // "

        footer += "Synth Music 2024"

        embed.set_footer(text=footer, icon_url=bot.get_avatar())

        return embed

    @staticmethod
    async def play_track(
        bot: Bot,
        interaction: disnake.ApplicationCommandInteraction,
        player: wavelink.Player,
        embed: disnake.Embed,
        volume: int,
    ) -> None:
        if not player.playing:
            if not player.current:
                await player.set_volume(min(100, max(1, volume)))
            # embed = await self.music_embed(interaction, track)
            message = await interaction.channel.send(content="Waiting...")
            await interaction.delete_original_response(delay=2)

            track = player.queue.get()

            setattr(player, "message", message)
            player.inactive_timeout = 300

            await player.play(track, add_history=False)

        else:
            await interaction.edit_original_response(content=None, embed=embed)
            await interaction.delete_original_response(delay=5)

        await player.message.edit(  # type: ignore
            view=NavigationPanel(
                bot,
                (await interaction.original_response()).id,
                history_exists=False,
                player=player,
                interaction=interaction,
            )
        )

    @staticmethod
    async def skip_track(
        player: wavelink.Player,
        interaction: disnake.ApplicationCommandInteraction,
        previous: bool = False,
    ) -> None:
        embed = CustomEmbed(
            author=interaction.user,  # type: ignore
            title="Track skipped",
            description=(
                f"Skipped the **[{player.current.title}]({str(player.current.uri)})**.\n"
                f"Now playing: **[{player.queue[0].title}]({str(player.queue[0].uri)})**."
            ),
            color=BasicColors.SUCCESS,
        ).get_embed()

        await interaction.delete_original_response()  # TODO: В ідеалі нам тут нічого відповідати не треба, бо це калл, але я хз, башка не робить.
        await player.message.reply(embed=embed)  # type: ignore
        await player.skip()

        if previous:
            player.queue.history.remove(player.current)

            await player.message.edit(  # type: ignore
                view=NavigationPanel(
                    bot,
                    (await interaction.original_response()).id,
                    history_exists=False,
                    player=player,
                    interaction=interaction,
                )
            )

    @staticmethod
    async def set_volume(player: wavelink.Player, volume: int) -> None:
        embed: disnake.Embed = player.message.embeds[0]  # type: ignore
        embed.set_footer(
            text=f"Volume: {volume}% // Synth Music 2024", icon_url=bot.get_avatar()
        )
        await player.message.edit(embed=embed)  # type: ignore
        await player.set_volume(min(100, max(1, volume)))

    @staticmethod
    async def disconnect(interaction: disnake.ApplicationCommandInteraction) -> None:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player:
            return await interaction.response.send_message(
                embed=CustomEmbed.error_embed(
                    author=interaction.user,
                    title="<:crossmark:1282338837456224394> | I am not in a voice channel",
                ).get_embed(),
                ephemeral=True,
            )

        await player.disconnect()
        await player.message.edit(  # type: ignore
            embed=CustomEmbed.error_embed(
                author=interaction.user,
                title=f"<:disconnect:1279835624257486868> Disconnected from voice channel",
            ).get_embed(),
            ephemeral=True,
            view=None,
        )
        await interaction.delete_original_response()

    @staticmethod
    async def display_queue(interaction: disnake.ApplicationCommandInteraction) -> None:
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        await MusicError.check_basic(interaction)
        await MusicError.check_queue(interaction)
        # await MusicFunctions.check_for_error(interaction)

        queue_ = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )
        queue_list = list(enumerate(queue_, start=1))

        """
        requested_by = (
                (
                    await (
                        await self.bot.fetch_guild(self.player.guild.id)
                    ).fetch_member(int(track.extras.requested_by))
                ).name
                if hasattr(track.extras, "requested_by")
                else "Auto recommended"
            )
            """

        guild = interaction.guild

        embeds = [
            CustomEmbed(
                title=f"{interaction.guild.name}'s Queue",
                description="\n".join(
                    [
                        f"`[ {str(timedelta(seconds=round(music.length / 1000)))} ]` {music.title} // "
                        f"`{(await guild.get_or_fetch_member(int(music.extras.requested_by))) if hasattr(music.extras, 'requested_by') else 'Unknown'}`"
                        for _, music in queue_list[i : i + 10]
                        if music
                    ]
                ),
            ).get_embed()
            for i in range(0, len(queue_list), 10)
        ]

        paginator = CreatePaginator(embeds=embeds, author_id=interaction.author.id)
        await interaction.send(embed=embeds[0], view=paginator, ephemeral=True)

    @staticmethod
    async def shuffle_queue(interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer(ephemeral=True)

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        await MusicError.check_basic(interaction)
        await MusicError.check_queue(interaction)
        # await MusicFunctions.check_for_error(interaction)

        if not hasattr(player, "previous_queue"):
            player.previous_queue = player.queue.copy()

        if not hasattr(player, "previous_auto_queue"):
            player.previous_auto_queue = player.auto_queue.copy()

        (player.auto_queue if player.queue.is_empty else player.queue).shuffle()
        next_song = (
            player.queue[0] if not player.queue.is_empty else player.auto_queue[0]
        )

        embed = CustomEmbed(
            title="<:shuffle:1279835431315308605> Shuffled the queue",
            description=f"Current song: **{player.current.title}**\nNext song: **{next_song.title}**",
            color=BasicColors.SUCCESS,
        ).get_embed()

        await interaction.send(
            embed=embed,
            ephemeral=True,
            view=ShuffleView(
                bot, interaction, player.previous_queue, player.previous_auto_queue
            ),
        )

    async def toggle_player(
        self, interaction: disnake.ApplicationCommandInteraction
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        await player.pause(not player.paused)

        embed = CustomEmbed(
            title="⏸️ | Paused Player" if player.paused else "▶ | Resumed Player",
            description=f"Current song: **{player.current.title}**",
            color=BasicColors.SUCCESS,
        ).get_embed()

        main_embed = await self.nowplaying(interaction)

        await interaction.send(embed=embed, ephemeral=True)

        await player.message.edit(embed=main_embed)  # type: ignore
