from typing import cast, Union, Optional
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

from core.database.repositories.guild import GuildMusicRepository


@dataclass
class MusicFunctions:
    guild_repo = GuildMusicRepository()

    @staticmethod
    async def calculate_required_votes(player: wavelink.Player) -> int:
        voice_channel = player.channel
        members_in_vc = [member for member in voice_channel.members if not member.bot]
        return len(members_in_vc) // 2 + len(members_in_vc) % 2

    @staticmethod
    async def handle_skip_vote(
        interaction: disnake.ApplicationCommandInteraction,
        player: wavelink.Player,
        track: Optional[str] = None,
    ) -> None:
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if not hasattr(player, "skip_votes"):
            player.skip_votes: set[int] = set()  # type: ignore

        user_id = interaction.author.id
        required_votes = await MusicFunctions.calculate_required_votes(player)
        queue = MusicFunctions.get_player_queue(player)

        if user_id in player.skip_votes:
            player.skip_votes.remove(user_id)
            embed = CustomEmbed(
                title=f"<a:success:1282339093494943764> | Vote removed ({len(player.skip_votes)}/{required_votes}) to skip the current track!",
                author=interaction.author,
            ).get_embed()
            await interaction.send(embed=embed, ephemeral=True)
            return

        player.skip_votes.add(user_id)
        current_votes = len(player.skip_votes)

        if current_votes >= required_votes:
            if track:
                track_skipped = await MusicFunctions.skip_specific_track_in_queue(
                    player, track, queue, error_embed, interaction
                )
                if not track_skipped:
                    return
            await MusicFunctions.skip_track_action(player, interaction)
            player.skip_votes.clear()
        else:
            embed = CustomEmbed(
                title=f"<a:success:1282339093494943764> | Vote added ({current_votes}/{required_votes}) to skip the current track!",
                author=interaction.author,
                color=BasicColors.SUCCESS,
            ).get_embed()
            await interaction.send(embed=embed, ephemeral=True)

    @staticmethod
    async def handle_previous_vote(
        interaction: disnake.ApplicationCommandInteraction,
        player: wavelink.Player,
        track: Optional[str] = None,
    ) -> None:
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if not hasattr(player, "previous_votes"):
            player.previous_votes: set[int] = set()  # type: ignore

        required_votes = await MusicFunctions.calculate_required_votes(player)
        dj_role = await MusicFunctions.guild_repo.find_dj_role(interaction.guild.id)
        queue = MusicFunctions.get_player_queue(player)

        if dj_role and interaction.author.get_role(dj_role):
            if track:
                track_switched = await MusicFunctions.switch_to_specific_previous_track(
                    player, track, queue, error_embed, interaction
                )
                if not track_switched:
                    return
            else:
                await MusicFunctions.switch_to_previous_track_action(
                    player, interaction, queue
                )
            player.previous_votes.clear()
            return

        if interaction.author.id in player.previous_votes:
            player.previous_votes.remove(interaction.author.id)
            embed = CustomEmbed(
                title=f"<a:success:1282339093494943764> | Vote removed ({len(player.previous_votes)}/{required_votes}) to switch to the previous track!",
                author=interaction.author,
            ).get_embed()
            await interaction.send(embed=embed, ephemeral=True)
            return

        player.previous_votes.add(interaction.author.id)
        current_votes = len(player.previous_votes)

        if current_votes >= required_votes:
            if track:
                track_switched = await MusicFunctions.switch_to_specific_previous_track(
                    player, track, queue, error_embed, interaction
                )
                if not track_switched:
                    return
            else:
                await MusicFunctions.switch_to_previous_track_action(
                    player, interaction, queue
                )
            player.previous_votes.clear()
        else:
            embed = CustomEmbed(
                title=f"<a:success:1282339093494943764> | Vote added ({current_votes}/{required_votes}) to switch to the previous track!",
                author=interaction.author,
                color=BasicColors.SUCCESS,
            ).get_embed()
            await interaction.send(embed=embed, ephemeral=True)

    @staticmethod
    async def get_player_queue(player: wavelink.Player) -> wavelink.Queue:
        return (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                and not player.auto_queue.is_empty
                else player.queue
            )
        )

    @staticmethod
    async def skip_specific_track_in_queue(
        player: wavelink.Player,
        track_query: str,
        queue: wavelink.Queue,
        error_embed: disnake.Embed,
        interaction: disnake.ApplicationCommandInteraction,
    ) -> bool:
        for index, song in enumerate(queue):
            if track_query.lower() in f"{song.author} - {song.title}".lower():
                track = player.queue[index]
                player.queue.put_at(0, track)
                return True
        else:
            error_embed.title = "<:crossmark:1282338837456224394> | The specified track was not found in the queue!"
            await interaction.send(embed=error_embed, ephemeral=True)
            return False

    @staticmethod
    async def switch_to_specific_previous_track(
        player: wavelink.Player,
        track_query: str,
        queue: wavelink.Queue,
        error_embed: disnake.Embed,
        interaction: disnake.ApplicationCommandInteraction,
    ) -> bool:
        for song in queue.history:
            if track_query.lower() in f"{song.author} - {song.title}".lower():
                queue.put_at(0, song)
                return True
        else:
            error_embed.title = "<:crossmark:1282338837456224394> | The specified track was not found in history!"
            await interaction.send(embed=error_embed, ephemeral=True)
            return False

    @staticmethod
    async def skip_track_action(
        player: wavelink.Player, interaction: disnake.ApplicationCommandInteraction
    ) -> None:
        embed = CustomEmbed(
            author=interaction.user,
            title="Track Skipped",
            description=(
                f"Skipped **[{player.current.title}]({str(player.current.uri)})**.\n"
                f"{MusicFunctions.get_track_source(player.current)} Now playing: **[{player.queue[0].title}]({str(player.queue[0].uri)})**."
            ),
            color=BasicColors.SUCCESS,
        ).get_embed()

        await interaction.delete_original_response()
        await player.main_message.reply(embed=embed)
        await player.skip()

    @staticmethod
    async def switch_to_previous_track_action(
        player: wavelink.Player,
        interaction: disnake.ApplicationCommandInteraction,
        queue: wavelink.Queue,
    ) -> None:
        previous_track = queue.history.get()
        queue.put_at(0, previous_track)
        queue.put_at(1, player.current)

        embed = CustomEmbed(
            author=interaction.user,
            title="Switching to Previous Track",
            description=(
                f"Switching to previous track **[{previous_track.title}]({str(previous_track.uri)})**.\n"
                f"{MusicFunctions.get_track_source(player.current)} Now playing: **[{previous_track.title}]({str(previous_track.uri)})**."
            ),
            color=BasicColors.SUCCESS,
        ).get_embed()

        await interaction.delete_original_response()
        await player.main_message.reply(embed=embed)
        await player.skip()

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
        try:
            embed.add_field(
                name="Duration:",
                value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
                inline=True,
            )
        except OverflowError:
            pass

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
            author=requested,
            title=f"{MusicFunctions.get_track_source(track)} Now playing",
            image=track.artwork,
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

            message = await interaction.channel.send(content="Waiting...")
            await interaction.delete_original_response(delay=2)

            track = player.queue.get()

            player.inactive_timeout = 300
            player.main_message = message

            await player.play(track, add_history=False)

        else:
            await interaction.edit_original_response(content=None, embed=embed)
            await interaction.delete_original_response(delay=5)

        await player.main_message.edit(
            view=NavigationPanel(
                bot,
                (await interaction.original_response()).id,
                history_exists=False,
                player=player,
                interaction=interaction,
            )
        )

    @staticmethod
    def get_track_source(track: wavelink.Playable) -> str:
        emojis = {
            "youtube": "<:youtube:1279826494847451199>",
            # "youtubemusic": "<:youtube:1279826494847451199>",
            "soundcloud": "<:soundcloud:1285240280135766058>",
            "spotify": "<:spotify:1284447177082408990>",
            "applemusic": "<:applemusic:1285240602014908507>",
            "deezer": "<:deezer:1285240923432681483>",
        }
        return emojis.get(track.source)

    @staticmethod
    async def skip_track(
        player: wavelink.Player,
        interaction: disnake.ApplicationCommandInteraction,
        previous: bool = False,
    ) -> None:
        embed = CustomEmbed(
            author=interaction.user,
            title="Track skipped",
            description=(
                f"Skipped the **[{player.current.title}]({str(player.current.uri)})**.\n"
                f"{MusicFunctions.get_track_source(player.current)} Now playing: **[{player.queue[0].title}]({str(player.queue[0].uri)})**."
            ),
            color=BasicColors.SUCCESS,
        ).get_embed()

        await interaction.delete_original_response()
        await player.main_message.reply(embed=embed)
        await player.skip()

        if previous:
            player.queue.history.remove(player.current)

            await player.main_message.edit(
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
        embed: disnake.Embed = player.main_message.embeds[0]
        embed.set_footer(
            text=f"Volume: {volume}% // Synth Music 2024", icon_url=bot.get_avatar()
        )
        await player.main_message.edit(embed=embed)
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
            )

        await player.disconnect()
        await player.main_message.edit(
            embed=CustomEmbed.error_embed(
                author=interaction.user,
                title=f"<:disconnect:1279835624257486868> Disconnected from voice channel",
            ).get_embed(),
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

        guild = interaction.guild

        embeds = [
            CustomEmbed(
                title=f"{interaction.guild.name}'s Queue",
                description="\n".join(
                    [
                        f"`[ {str(timedelta(seconds=round(music.length / 1000)))} ]` {MusicFunctions.get_track_source(music)} {music.title} // "
                        f"`{(await guild.get_or_fetch_member(int(music.extras.requested_by))) if hasattr(music.extras, 'requested_by') else 'Unknown'}` // "
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
            description=(
                f"{MusicFunctions.get_track_source(player.current)} Current song: **{player.current.title}**"
                f"\n{MusicFunctions.get_track_source(next_song)} Next song: **{next_song.title}**"
            ),
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
            description=f"{MusicFunctions.get_track_source(player.current)} Current song: **{player.current.title}**",
            color=BasicColors.SUCCESS,
        ).get_embed()

        main_embed = await self.nowplaying(interaction)

        await interaction.send(embed=embed, ephemeral=True)

        await player.main_message.edit(embed=main_embed)
