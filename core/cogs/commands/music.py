from typing import cast
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
        nodes = [wavelink.Node(uri="http://localhost:2333", password="youshallnotpass")]

        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, _: wavelink.NodeReadyEventPayload) -> None:
        logger.info("[+] Wavelink Node ready")

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload: wavelink.TrackEndEventPayload
    ) -> None:
        try:
            old_message = await payload.player.interaction.original_response()

            try:
                await old_message.delete()
            except (disnake.NotFound, AttributeError):
                pass

            new_track = payload.player.queue.get()

            """
            when track ends: player - old_track
            new_track: payload.player.queue.get()

            if last_track defined:
                queue.put_at(0, last_track)
                queue.history.remove(old_track)
                
            """

            if getattr(payload.player, "last_track", None):
                new_track = payload.player.last_track

                payload.player.queue.put_at(0, new_track)
                payload.player.queue.history.remove(payload.track)
                await payload.player.play(new_track, add_history=False)

            else:
                await payload.player.play(new_track)

            logger.info(
                f"[+] New Track Started: {new_track.title} by {new_track.author}"
            )

            embed = custom_embed()
            embed.title = f"Now playing - {new_track.title}"

            embed.description = f"[{new_track.title}]({str(new_track.uri)})"
            embed.add_field(
                name="Artist:", value=f"**`{new_track.author}`**", inline=True
            )
            embed.add_field(
                name="Duration:",
                value=f"`{str(timedelta(seconds=round(new_track.length / 1000)))}`",
                inline=True,
            )
            embed.set_image(url=new_track.artwork)

            message = await payload.player.interaction.followup.send(embed=embed)
            await message.edit(
                embed=embed,
                view=NavigationPanel(self.bot, message.id),
            )

        except wavelink.QueueEmpty:
            await payload.player.interaction.send(f"Queue is empty")

    @commands.slash_command(description="Search and play music from Spotify")
    async def play(
        self, interaction: disnake.MessageCommandInteraction, *, query: str = None
    ):
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

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        #! assert isinstance(player, wavelink.Player)

        try:
            player: wavelink.Player = await interaction.user.voice.channel.connect(
                cls=wavelink.Player
            )
        except disnake.ClientException as e:
            error_embed.title = (
                "I was unable to join this voice channel. Please try again."
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        tracks: wavelink.Search = await wavelink.Playable.search(
            query, source=wavelink.TrackSource.YouTube
        )

        if not tracks:
            error_embed.title = (
                "Could not find any tracks with that query. Please try again."
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            embed.title = f"Added playlist **{tracks.name}** ({added} songs) to the queue."

            track: wavelink.Playable = tracks[0] if not player.current else player.current

            embed.description = (
                f"Now playing - [{track.title}]({str(track.uri)})"
            ) 
            embed.add_field(name="Artist:", value=f"**`{track.author}`**", inline=True)
            embed.add_field(
                name="Duration:",
                value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
                inline=True,
            )
            embed.set_image(url=track.artwork)

            await interaction.response.defer()
            message = await interaction.followup.send(embed=embed, ephemeral=True)
            await message.edit(
                embed=embed,
                view=NavigationPanel(self.bot, message.id),
            )

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
            message = await interaction.followup.send(embed=embed, ephemeral=True)
            await message.edit(
                embed=embed,
                view=NavigationPanel(self.bot, message.id),
            )

        if not player.playing:
            setattr(player, "interaction", interaction)
            await player.play(player.queue.get(), volume=100)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
