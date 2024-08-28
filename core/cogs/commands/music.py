from datetime import timedelta

import wavelink

import disnake
from disnake.ext import commands

from core.misc.views.music import NavigationPanel
from core.misc.embed import custom_embed
from core.logger.logger import logger


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self) -> None:
        nodes = [wavelink.Node(uri="http://localhost:2333", password="weever_gay")]

        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, _: wavelink.NodeReadyEventPayload) -> None:
        logger.info("[+] Wavelink Node ready")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        if (
            payload.player
            and hasattr(payload.player, "auto_play_tracks")
            and payload.original
            and payload.original.recommended
        ):
            track: wavelink.Playable = payload.track

            print(f"\n\n`This track was recommended via {track.source}`")

            payload.player.queue.put_at(0, track)
            payload.player.queue.put_at(1, payload.player.current)
            payload.player.queue.history.put_at(0, payload.player.current)
            
            await payload.player.play(track, add_history=False)

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload: wavelink.TrackEndEventPayload
    ) -> None:
        if payload.player and (payload.player.queue and payload.player.queue.is_empty):
            return await payload.player.interaction.send("Queue is empty")

        try:
            (
                await (await payload.player.interaction.original_response()).delete()
                if payload.player
                else None
            )
        except (disnake.NotFound, AttributeError):
            pass

        """
        Explanation:

        When the track ends, the player will play the next track in the queue, 
        but before that it adds previous track to the new attribute

        So there is scheme:

        1. previous equals old_track
        2. new_player gets from queue
        3. new_player plays new_track
        """

        if not payload.player.queue and payload.player.queue.count >= 1:
            new_track = payload.original
            setattr(payload.player, "auto_play_tracks", True)

            await payload.player.play(new_track, add_history=False)
        else:
            new_track = payload.player.queue.get()

        logger.info(f"[+] New Track Started: {new_track.title} by {new_track.author}")

        embed = custom_embed()
        embed.title = f"Now playing - {new_track.title}"

        embed.description = f"[{new_track.title}]({str(new_track.uri)})"
        embed.add_field(name="Artist:", value=f"`{new_track.author}`", inline=True)
        embed.add_field(
            name="Duration:",
            value=f"`{str(timedelta(seconds=round(new_track.length / 1000)))}`",
            inline=True,
        )
        embed.set_image(url=new_track.artwork)

        message = await payload.player.interaction.followup.send(embed=embed)

        history_exists = payload.player.queue.history.count > 0

        await message.edit(
            embed=embed,
            view=NavigationPanel(
                self.bot,
                message.id,
                player=payload.player,
                history_exists=history_exists,
            ),
        )

        await payload.player.play(new_track, add_history=False)

    @commands.slash_command(
        description="Search and play music from Youtube/Spotify/SoundCloud/Deezer/Apple Music"
    )
    async def play(self, interaction: disnake.MessageCommandInteraction, *, query: str):
        embed = custom_embed()
        error_embed = custom_embed(color=disnake.Color.red())

        if not query:
            error_embed.title = (
                "Query is not provided. Please enter a query and try again."
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        elif not getattr(interaction.author.voice, "channel", None):
            error_embed.title = "You are not in a voice channel. Please join a voice channel and try again."
            return await interaction.send(embed=error_embed, ephemeral=True)

        elif not interaction.guild.voice_client:
            player: wavelink.Player = await interaction.author.voice.channel.connect(
                cls=wavelink.Player
            )
        else:
            player: wavelink.Player = interaction.guild.voice_client

        tracks: wavelink.Search = await wavelink.Playable.search(
            query, source=wavelink.TrackSource.YouTubeMusic
        )

        if not tracks:
            error_embed.title = (
                "Could not find any tracks with that query. Please try again."
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)

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

            embed.title = f"{'Now playing' if not player.playing else 'Added to queue'} - {track.title}"

            embed.description = f"[{track.title}]({str(track.uri)})"
            embed.add_field(name="Artist:", value=f"**`{track.author}`**", inline=True)
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
            await player.play(track, add_history=False)

        history_exists = player.queue.history.count > 0

        await message.edit(
            embed=embed,
            view=NavigationPanel(
                self.bot,
                message.id,
                history_exists=history_exists,
                player=player,
            ),
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
