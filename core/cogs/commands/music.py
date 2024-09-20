from typing import cast

import disnake
import wavelink
from disnake.ext import commands

from core.misc.music.functions import MusicFunctions
from core.misc.music.errors import MusicError

from core.database.repositories.music import MusicRepository
from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()
        self.bot: commands.Bot = bot

        self.repository = MusicRepository()
        self.functions = MusicFunctions()
        self.errors = MusicError()

    @commands.slash_command()
    async def player(self, _) -> None:
        pass

    @player.sub_command(description="Search and play music from nearly any platform")
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        *,
        query: str,
        volume: int = commands.Param(default=75, max_length=3, min_length=1),
    ) -> None:

        player: wavelink.Player = (
            interaction.guild.voice_client
            or await interaction.author.voice.channel.connect(cls=wavelink.Player)
        )
        await interaction.me.edit(deafen=True)

        await self.errors.check_basic(interaction, query)

        await interaction.send(
            "<a:loading:1281259173639884882> Searching for tracks...",
            ephemeral=True,
        )

        if any(tag in query.lower() for tag in ["history:", "found:"]):
            tag, query = query.split(" ", maxsplit=1)

            if tag.lower().startswith("history:"):
                query = (
                    await MusicRepository().find_song(
                        author_id=interaction.author.id, query=query
                    )
                ).url

        tracks: wavelink.Search = await wavelink.Playable.search(
            query, source="spsearch"
        )

        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if not tracks:
            error_embed.title = "<:crossmark:1282338837456224394> | Could not find any tracks with that query"
            await interaction.edit_original_response(content=None, embed=error_embed)
            return None

        if isinstance(tracks, wavelink.Playlist):
            for track in tracks.tracks:
                track.extras = {"requested_by": interaction.author.id}

            added: int = await player.queue.put_wait(tracks)
            track_info = {"track": f"{tracks.name} — {added} songs", "url": query}

            embed = CustomEmbed(
                title=f"Added playlist **{tracks.name}** ({added} songs) to the queue",
                author=interaction.author,
                footer_text=f"Volume: {player.volume}% // Synth Music 2024",
            ).get_embed()

            # track: wavelink.Playable = (
            #     tracks[0] if not player.current else player.current
            # )

        else:
            track: wavelink.Playable = tracks[0]
            track.extras = {"requested_by": interaction.author.id}

            await player.queue.put_wait(track)

            track_info = {
                "track": f"{track.title} — {track.author}",
                "url": track.uri,
                "source": track.source,
            }

            embed = CustomEmbed(
                title=f"Added track **{track.title}** to the queue",
                author=interaction.author,
                color=BasicColors.SUCCESS,
                footer_text=f"Volume: {player.volume}% // Synth Music 2024",
            ).get_embed()

        await self.repository.save_song(interaction.author.id, track_info)
        await self.functions.play_track(self.bot, interaction, player, embed, volume)

    @player.sub_command(name="skip", description="Skip the current track")
    async def skip(
        self, interaction: disnake.ApplicationCommandInteraction, track: str = None
    ):
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        queue = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )

        await self.errors.check_basic(interaction)
        await self.errors.check_queue(interaction)

        if track:
            for index, song in enumerate(queue):
                if track.lower() in f"{song.author} - {song.title}".lower():
                    track = player.queue[index]
                    player.queue.put_at(0, track)
                    break
            else:
                error_embed.title = "<:crossmark:1282338837456224394> | The specified track was not found in the queue!"
                return await interaction.send(embed=error_embed, ephemeral=True)

        await self.functions.skip_track(player, interaction)

    @player.sub_command(name="previous", description="Switch to the previous track(s)")
    async def previous(
        self, interaction: disnake.ApplicationCommandInteraction, track: str = None
    ):
        await interaction.response.defer(ephemeral=True)

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        queue = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )

        await self.errors.check_basic(interaction)

        if not track:
            previous_track = queue.history.get()
            queue.put_at(0, previous_track)
            queue.put_at(1, player.current)

        else:
            for index, song in enumerate(queue.history):
                if track.lower() in f"{song.author} - {song.title}".lower():
                    track = queue.history[index]
                    queue.put_at(0, track)
                    queue.put_at(1, player.current)
                    break
            else:
                error_embed.title = "<:crossmark:1282338837456224394> | The specified track was not found in the queue!"
                return await interaction.send(embed=error_embed, ephemeral=True)

        await self.functions.skip_track(player, interaction, True)

    @player.sub_command(name="volume", description="Set the track volume")
    async def volume(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        volume: int = commands.Param(
            default=75, max_length=3, min_length=1, choices=[10, 50, 75, 100]
        ),
    ):
        await interaction.response.defer(ephemeral=True)

        volume = min(100, max(1, volume))

        await self.errors.check_basic(interaction)
        embed = await self.errors.check_error_volume(interaction, volume)

        await interaction.send(
            embed=embed,
            ephemeral=True,
        )

    @player.sub_command(name="queue", description="See all song in the queue")
    async def queue(self, interaction: disnake.ApplicationCommandInteraction):
        await self.functions.display_queue(interaction)

    @player.sub_command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: disnake.ApplicationCommandInteraction):
        await self.functions.shuffle_queue(interaction)

    @player.sub_command(
        name="toggle", description="Toggle player status (paused/resumed)"
    )
    async def toggle(self, interaction: disnake.ApplicationCommandInteraction):
        await self.functions.toggle_player(interaction)

    @player.sub_command(name="nowplaying", description="See the current playing track")
    async def nowplaying(self, interaction: disnake.ApplicationCommandInteraction):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player:
            embed = CustomEmbed.error_embed(
                author=interaction.author,
                title="<:crossmark:1282338837456224394> | I am not in a voice channel!",
            ).get_embed()

            return await interaction.send(
                embed=embed,
                ephemeral=True,
            )

        elif (
            not interaction.author.voice
            or interaction.author.voice.channel != player.channel
        ):
            embed = CustomEmbed.error_embed(
                author=interaction.author,
                title="<:crossmark:1282338837456224394> | You are not in a voice channel",
            ).get_embed()

            return await interaction.send(
                embed=embed,
                ephemeral=True,
            )

        if not player.current:
            embed = CustomEmbed.error_embed(
                author=interaction.author,
                title="<:crossmark:1282338837456224394> | No track is currently playing",
            ).get_embed()

            return await interaction.send(
                embed=embed,
                ephemeral=True,
            )

        await interaction.send(
            embed=await self.functions.nowplaying(interaction), ephemeral=True
        )

    @player.sub_command(
        name="disconnect", description="Disconnect from the voice channel"
    )
    async def disconnect(self, interaction: disnake.ApplicationCommandInteraction):
        await self.functions.disconnect(interaction)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
