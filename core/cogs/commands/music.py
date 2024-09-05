from datetime import timedelta
from typing import cast

import disnake
import wavelink
from disnake.ext import commands

from core.database.models.music import MusicModel, Song
from core.misc.embed import custom_embed
from core.misc.misc import create_ping_command_string
from core.misc.views.music.panel import NavigationPanel


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()
        self.bot = bot

    @commands.slash_command(
        # description="Search, play, stop, pause, resume, skip, and queue music from YouTube/Spotify/SoundCloud/Deezer/Apple Music"
    )
    async def player(self, _) -> None:
        pass

    @player.sub_command(
        description="Search and play music from YouTube/Spotify/SoundCloud/Deezer/Apple Music"
    )
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        *,
        query: str,
        volume: int = commands.Param(default=100, max_length=3, min_length=1),
    ):
        embed = custom_embed()
        error_embed = custom_embed(color=disnake.Color.red())

        if query.startswith("❌"):
            error_embed.title = (
                "Query is not provided. Please enter a query and try again."
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        if not interaction.guild.voice_client:
            player: wavelink.Player = await interaction.author.voice.channel.connect(
                cls=wavelink.Player
            )
        else:
            player: wavelink.Player = cast(
                wavelink.Player, interaction.guild.voice_client
            )

        if " — " in query:
            # if getattr(interaction, "is_autocomplete", False):
            # delattr(interaction, "is_autocomplete")
            track_info = await MusicModel.filter(user_id=interaction.author.id).first()
            if track_info:
                song = await Song.filter(name=query).first()
                if song:
                    query = song.url

        tracks: wavelink.Search = await wavelink.Playable.search(query)

        if not tracks:
            error_embed.title = (
                "Could not find any tracks with that query. Please try again."
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            track_info = {"track": f"{tracks.name} — {added} songs", "url": query}

            embed.title = (
                f"Added playlist **{tracks.name}** ({added} songs) to the queue."
            )
            track: wavelink.Playable = (
                tracks[0] if not player.current else player.current
            )
            embed.description = f"Now playing - [{track.title}]({str(track.uri)})"
            embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
            embed.add_field(
                name="Duration:",
                value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
                inline=True,
            )
            embed.set_image(url=track.artwork)

        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            track_info = {
                "track": f"{track.title} — {track.author}",
                "url": track.uri,
                "source": track.source,
            }

            embed.title = f"{'Now playing' if not player.playing else 'Added to queue'} - {track.title}"
            embed.description = f"[{track.title}]({str(track.uri)})"
            embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
            embed.add_field(
                name="Duration:",
                value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
                inline=True,
            )
            embed.set_image(url=track.artwork)

        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)

        if not player.playing:
            track = player.queue.get()
            setattr(player, "interaction", interaction)
            setattr(player, "first_play", True)
            await player.play(track, add_history=False)

        volume = min(100, max(1, volume))
        await player.set_volume(volume)

        history_exists = player.queue.history.count > 0

        result = await MusicModel.get_or_none(
            user_id=interaction.author.id
        ).prefetch_related("songs")
        if not result:
            music_model = await MusicModel.create(user_id=interaction.author.id)
            song = await Song.create(name=track_info["track"], url=track_info["url"])
            await music_model.songs.add(song)
        else:
            if not await result.songs.filter(url=track_info["url"]).exists():
                if len(result.songs) >= 3:
                    await result.songs.remove(result.songs[0])
                await result.songs.add(
                    await Song.create(name=track_info["track"], url=track_info["url"])
                )

        await message.edit(
            embed=embed,
            view=NavigationPanel(
                self.bot,
                message.id,
                history_exists=history_exists,
                player=player,
            ),
        )

    @play.autocomplete("query")
    async def play_autocomplete(
        self, interaction: disnake.ApplicationCommandInteraction, search_query: str
    ):
        if not interaction.author.voice:
            await interaction.response.autocomplete(
                choices=["❌ | You are not in a voice channel"]
            )
            return

        # setattr(interaction, "is_autocomplete", True)

        if not search_query:
            result = await MusicModel.filter(user_id=interaction.author.id).first()

            autocomplete_list = (
                [song.name for song in (await result.songs.all())]
                if result
                else ["❌ | Try to add a song for the first time"]
            )

            await interaction.response.autocomplete(choices=autocomplete_list)
            return

        search_results = await wavelink.Playable.search(search_query)

        autocomplete_options = [
            f"{track.title} — {track.author}"
            for index, track in enumerate(search_results, start=1)
            if len(f"{track.title} — {track.author}") <= 100 and index < 25
        ]

        await interaction.response.autocomplete(choices=autocomplete_options)

    # @player.sub_command(
    #     description="Skip the current song",
    # )
    # async def skip(self, interaction: disnake.ApplicationCommandInteraction):
    #     embed = custom_embed()
    #     error_embed = custom_embed(color=disnake.Color.red())
    #     if not interaction.guild.voice_client:
    #         error_embed.title = "❌ | You are not connected to a voice channel"
    #         return await interaction.response.send_message(embed=error_embed)

    #     player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
