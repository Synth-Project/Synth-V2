from datetime import timedelta
from typing import cast

import disnake
import wavelink
from disnake.ext import commands

from core.database.models.music import MusicModel, Song
from core.misc.color import BasicColors
from core.misc.embed import custom_embed
from core.misc.misc import shorten_text
from core.misc.views.music.panel import NavigationPanel


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()
        self.bot = bot

    @commands.slash_command()
    async def player(self, _) -> None:
        pass

    @player.sub_command(description="Search and play music from nearly any platform")
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        *,
        query: str,
        volume: int = commands.Param(default=100, max_length=3, min_length=1),
    ):
        """
        Search and play music from nearly any platform

        Parameters:
            query (str): The query to search for
            volume (int): The volume to set the player to (default is 100)

        Returns:
            None
        """
        embed = custom_embed(author=interaction.author)
        error_embed = custom_embed(color=BasicColors.ERROR, author=interaction.author)

        if query.startswith("❌"):
            error_embed.title = (
                "Query is not provided. Please enter a query and re-invoke the command."
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        await interaction.response.send_message(
            "<a:loading:1281259173639884882> Searching for tracks..."
        )

        if not interaction.guild.voice_client:
            player: wavelink.Player = await interaction.author.voice.channel.connect(
                cls=wavelink.Player
            )
        else:
            player: wavelink.Player = cast(
                wavelink.Player, interaction.guild.voice_client
            )

        if any(tag in query for tag in ["history:", "autocomplete:"]):
            tag, query = query.split(" ", maxsplit=1)

            if tag.startswith("history:"):
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
            return await interaction.edit_original_response(embed=error_embed)

        if isinstance(tracks, wavelink.Playlist):
            for track in tracks.tracks:
                track.extras = {"requested_by": interaction.author.id}

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
            track.extras = {"requested_by": interaction.author.id}

            await player.queue.put_wait(track)

            track_info = {
                "track": f"{track.title} — {track.author}",
                "url": track.uri,
                "source": track.source,
            }

            embed.title = f"{track.title}"
            embed.url = str(track.uri)

            embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
            embed.add_field(
                name="Duration:",
                value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
                inline=True,
            )
            embed.set_image(url=track.artwork)

        embed.set_footer(
            icon_url=interaction.bot.user.display_avatar.url,
            text=f"Volume: {player.volume}% // Synth Music 2024",
        )
        await interaction.edit_original_response(content=None, embed=embed)

        if not player.playing:
            track = player.queue.get()
            setattr(player, "interaction", interaction)
            setattr(player, "first_play", True)
            player.inactive_timeout = 300
            await player.play(track, add_history=False)

        if not player.playing or not player.current:
            await player.set_volume(min(100, max(1, volume)))

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

        await interaction.edit_original_response(
            embed=embed,
            view=NavigationPanel(
                self.bot,
                (await interaction.original_response()).id,
                history_exists=history_exists,
                player=player,
                interaction=interaction,
            ),
        )

    @play.autocomplete("query")
    async def play_autocomplete(
        self, interaction: disnake.ApplicationCommandInteraction, search_query: str
    ):
        """Autocomplete for the music play command

        If the user is not in a voice channel, returns a single option
        that tells the user to join a voice channel first.

        If the search query is empty, returns a list of all the songs the
        user has played before.

        Otherwise, searches for the given query and returns up to 25
        results.

        :param interaction: The interaction that triggered this autocomplete
        :type interaction: disnake.ApplicationCommandInteraction
        :param search_query: The search query given by the user
        :type search_query: str
        """

        if not interaction.author.voice:
            return await interaction.response.autocomplete(
                choices=["❌ | You are not in a voice channel"]
            )

        if not search_query:
            result = await MusicModel.filter(user_id=interaction.author.id).first()

            autocomplete_list = (
                [f"History: {shorten_text(song.name)}" for song in (await result.songs.all())]
                if result
                else ["❌ | Try to add a song for the first time"]
            )

            return await interaction.response.autocomplete(choices=autocomplete_list)

        search_results = await wavelink.Playable.search(search_query)
        autocomplete_options = [
            f"Founded: {shorten_text(f'{track.title} — {track.author}')}"
            for index, track in enumerate(search_results)
            if index < 25
        ]

        if not autocomplete_options:
            autocomplete_options = ["❌ | No results found"]

        await interaction.response.autocomplete(choices=autocomplete_options)

    # TODO: Add subcommands: previous, next, volume, shuffle, queue, effects, pause, resume


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
