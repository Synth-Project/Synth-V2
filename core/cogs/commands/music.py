from typing import cast

import disnake
import wavelink
from disnake.ext import commands

from core.cogs.autocomplete import play_autocomplete

from core.database.repositories.music import MusicRepository
from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed
from core.misc.music.functions import MusicFunctions


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()
        self.bot = bot

    async def cog_load(self) -> None:
        player = self.bot.get_slash_command("player")

        (
            (play := player.children.get("play"))
            and play.autocomplete("query")(play_autocomplete)
        )
        (
            (skip := player.children.get("skip"))
            and skip.autocomplete("track")(play_autocomplete)
        )

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

    @player.sub_command(name="skip", description="Skip the current track")
    async def skip(
        self, interaction: disnake.ApplicationCommandInteraction, track: str = None
    ):
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player:
            return await interaction.response.send_message(
                "❌ | No active player found!", ephemeral=True
            )

        if track:
            for index, song in enumerate(player.queue):
                if track.lower() in f"{song.author} - {song.title}".lower():
                    track = player.queue[index]
                    player.queue.put_at(0, track)
                    break
            else:
                return await interaction.response.send_message(
                    "❌ | The specified track was not found in the queue!",
                    ephemeral=True,
                )

        await MusicFunctions().skip_track(player, interaction)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
