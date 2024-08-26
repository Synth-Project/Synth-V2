import datetime
from collections import defaultdict
from typing import Dict, List, cast

import mafic
import wavelink

import disnake
from disnake.ext import commands
from disnake.ui import View

from core.misc.embed import custom_embed  # noqa


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()
        self.bot = bot
        bot.loop.create_task(self.add_nodes())

    async def add_nodes(self) -> None:
        nodes = [wavelink.Node(uri="http://localhost:2333", password="youshallnotpass")]

        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(
        self, payload: wavelink.NodeReadyEventPayload
    ) -> None:
        print(
            "Wavelink Node connected: %r | Resumed: %s", payload.node, payload.resumed
        )

    async def on_wavelink_node_ready(
        self, payload: wavelink.NodeReadyEventPayload
    ) -> None:
        print(
            "Wavelink Node connected: %r | Resumed: %s", payload.node, payload.resumed
        )

    @commands.slash_command(description="Search and play music from Spotify")
    async def play(self, interaction: disnake.MessageCommandInteraction, *, query: str):
        if not interaction.guild:
            return

        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

        try:
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)  # type: ignore
        except AttributeError:
            await interaction.send(
                "Please join a voice channel first before using this command."
            )
            await interaction.send(
                "Please join a voice channel first before using this command."
            )
            return
        except disnake.ClientException:
            await interaction.send(
                "I was unable to join this voice channel. Please try again."
            )
            await interaction.send(
                "I was unable to join this voice channel. Please try again."
            )
            return

        # Turn on AutoPlay to enabled mode.
        # enabled = AutoPlay will play songs for us and fetch recommendations...
        # partial = AutoPlay will play songs for us, but WILL NOT fetch recommendations...
        # disabled = AutoPlay will do nothing...
        player.autoplay = wavelink.AutoPlayMode.enabled

        # Lock the player to this channel...
        if not hasattr(player, "home"):
            player.home = interaction.channel
        elif player.home != interaction.channel:
            await interaction.send(
                f"You can only play songs in {player.home.mention}, as the player has already started there."
            )
            await interaction.send(
                f"You can only play songs in {player.home.mention}, as the player has already started there."
            )
            return

        # This will handle fetching Tracks and Playlists...
        # Seed the doc strings for more information on this method...
        # If spotify is enabled via LavaSrc, this will automatically fetch Spotify tracks if you pass a URL...
        # Defaults to YouTube for non URL based queries...
        tracks: wavelink.Search = await wavelink.Playable.search(
            query, source=wavelink.TrackSource.YouTube
        )
        tracks: wavelink.Search = await wavelink.Playable.search(
            query, source=wavelink.TrackSource.YouTube
        )
        if not tracks:
            await interaction.send(
                f"{interaction.user.mention} - Could not find any tracks with that query. Please try again."
            )
            await interaction.send(
                f"{interaction.user.mention} - Could not find any tracks with that query. Please try again."
            )
            return

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            await interaction.send(
                f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue."
            )
            await interaction.send(
                f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue."
            )
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await interaction.send(f"Added **`{track}`** to the queue.")

        if not player.playing:
            await player.play(player.queue.get(), volume=30)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
