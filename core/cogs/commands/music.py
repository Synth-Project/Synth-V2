from typing import cast

import disnake
import wavelink
from disnake.ext import commands

from core.database.repositories.music import MusicRepository
from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed
from core.misc.misc import shorten_text
from core.misc.music.functions import MusicFunctions


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
        volume: int = commands.Param(default=75, max_length=3, min_length=1),
    ) -> None:
        """
        Search and play music from nearly any platform

        Parameters:
            query (str): The query to search for
            volume (int): The volume to set the player to (default is 75)

        Returns:
            None
        """
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if query.startswith("❌"):
            query = query.replace("❌ | ", "")
            error_embed.title = query
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        player: wavelink.Player = (
            interaction.guild.voice_client
            or await interaction.author.voice.channel.connect(cls=wavelink.Player)
        )
        await interaction.me.edit(deafen=True)

        await interaction.response.send_message(
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

        tracks: wavelink.Search = await wavelink.Playable.search(query)

        if not tracks:
            error_embed.title = (
                "Could not find any tracks with that query. Please try again."
            )
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
            ).get_embed()

            track: wavelink.Playable = (
                tracks[0] if not player.current else player.current
            )

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
            ).get_embed()

        embed.set_footer(
            icon_url=interaction.bot.user.display_avatar.url,
            text=f"Volume: {player.volume}% // Synth Music 2024",
        )

        await MusicRepository().save_song(interaction.author.id, track_info)
        await MusicFunctions().play_track(
            self.bot, interaction, player, embed, track, volume
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
            result, _ = await MusicRepository().add_one(id=interaction.author.id)

            autocomplete_list = (
                [
                    f"History: {shorten_text(song.name)}"
                    for song in (await result.songs.all())
                ]
                if result
                else ["❌ | Try to add a song for the first time"]
            )

            return await interaction.response.autocomplete(choices=autocomplete_list)

        search_results = await wavelink.Playable.search(search_query)
        autocomplete_options = [
            f"Found: {shorten_text(f'{track.title} — {track.author}')}"
            for index, track in enumerate(search_results)
            if index < 25
        ]

        if not autocomplete_options:
            autocomplete_options = ["❌ | Could not find any tracks with that query"]

        await interaction.response.autocomplete(choices=autocomplete_options)

    @player.sub_command(name="skip", description="Skip the current track")
    async def skip(self, interaction: disnake.ApplicationCommandInteraction):
        """
        Skip the current track

        :param interaction: The interaction that triggered this command
        :type interaction: disnake.ApplicationCommandInteraction
        """

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        await MusicFunctions().skip_track(player, interaction)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
