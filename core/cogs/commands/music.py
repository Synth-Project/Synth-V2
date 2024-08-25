import datetime
from collections import defaultdict
from typing import Dict, List

import mafic

import disnake
from disnake.ext import commands
from disnake.ui import View

from core.misc.embed import EmbedPaginator, custom_embed


class MusicPlayer(mafic.Player[commands.Bot]):
    def __init__(
        self,
        client: commands.Bot,
        channel: disnake.VoiceChannel,
    ) -> None:
        super().__init__(client, channel)

        self.queue: List[mafic.Track] = []
        self.voice_channel: disnake.VoiceChannel = channel


class NavigationPanelView(View):
    def __init__(
        self, bot: commands.bot, message_id: int, *, timeout: float | None = None
    ) -> None:
        super().__init__(timeout=timeout)

        self.bot = bot
        self.message_id = message_id

    @disnake.ui.button(label="Skip", style=disnake.ButtonStyle.green, row=0)
    async def skip(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        player: MusicPlayer = interaction.guild.voice_client

        if not player or not player.queue:
            return await interaction.response.send_message(
                "Sorry, the music queue is empty!",
                ephemeral=True,
            )

        try:
            await player.stop()
            message = await interaction.channel.fetch_message(self.message_id)
            await message.delete()
            await interaction.response.defer()

        except (mafic.PlayerNotConnected, disnake.Forbidden):
            return await interaction.send(
                "Sorry, an error occurred while processing your request.",
                ephemeral=True,
            )

    @disnake.ui.button(label="Resume/Pause", style=disnake.ButtonStyle.gray, row=0)
    async def state_toggle(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: MusicPlayer = interaction.guild.voice_client
        assert player

        if player.paused:
            await player.resume()
            await interaction.response.edit_message(content="")
        else:
            await player.pause()
            await interaction.response.edit_message(content="")

    @disnake.ui.button(label="Volume", style=disnake.ButtonStyle.green, row=0)
    async def volume(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: MusicPlayer = interaction.guild.voice_client
        assert player

        modal = disnake.ui.Modal(
            title="Enter the volume",
            custom_id="volume",
            components=[
                disnake.ui.TextInput(
                    label="New volume:",
                    custom_id="new_volume",
                    style=disnake.TextInputStyle.short,
                )
            ],
        )
        await interaction.response.send_modal(modal=modal)

        response_modal = await self.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == "volume" and i.user == interaction.user,
        )

        new_volume = int(response_modal.text_values["new_volume"])

        if new_volume > 100 or new_volume < 1:
            return await response_modal.response.send_message(
                embed=custom_embed(
                    title=f"Please enter a number, between `1` and `100`",
                    color=disnake.Color.red(),
                ),
                ephemeral=True,
            )

        await player.set_volume(new_volume)
        await response_modal.response.send_message(
            embed=custom_embed(
                title=f"Set volume to {new_volume}", color=disnake.Color.green()
            ),
            ephemeral=True,
        )

    @disnake.ui.button(label="Queue", style=disnake.ButtonStyle.blurple, row=1)
    async def queue(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: MusicPlayer = interaction.guild.voice_client
        assert player

        embed = custom_embed(title="Music Queue")

        if len(player.queue) > 0:
            embed.description = "No music in the queue."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        for index, music in enumerate(player.queue, start=1):
            if index > 10:
                break

            embed.description += f"`{index}.` **{music.author} - {music.title}**\n"
            embed.set_footer(text="Page 0")

        paginator = EmbedPaginator(
            interaction, interaction.user, embed, player.queue[10:], None, 10
        )
        return await paginator.send_message(interaction)

    @disnake.ui.button(label="Disconnect", style=disnake.ButtonStyle.danger, row=1)
    async def dc(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        player: MusicPlayer = interaction.guild.voice_client
        assert player

        await player.disconnect()
        await interaction.response.send_message(
            embed=disnake.Embed(
                title="Disconnecting...",
                description="I have disconnected from voice channel",
                color=0x2F3236,
            ),
            ephemeral=True,
        )


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()

        self.bot = bot
        self.pool = mafic.NodePool(self.bot)
        self.channels: Dict[int, disnake.TextChannel] = defaultdict()  # noqa

        self.bot.loop.create_task(self.add_nodes())

    async def add_nodes(self) -> None:
        await self.pool.create_node(
            label="MAIN",
            host="localhost",
            port=2333,
            password="youshallnotpass",
        )

    @commands.slash_command(description="Search and play music from Spotify")
    async def play(
        self, interaction: disnake.MessageCommandInteraction, *, query: str = None
    ):
        error_embed = custom_embed(color=disnake.Color.red())

        if not query:
            error_embed.title = "Please provide a query or URL"
            return await interaction.send(embed=error_embed, ephemeral=True)

        if not getattr(interaction.author.voice, "channel", None):
            error_embed.title = "Join a voice channel first"
            return await interaction.send(embed=error_embed, ephemeral=True)

        voice = interaction.author.voice.channel
        player: MusicPlayer = interaction.guild.voice_client or await voice.connect(
            cls=MusicPlayer  # type: ignore
        )

        tracks = await player.fetch_tracks(query, search_type="spsearch")

        if not tracks:
            error_embed.title = f"`{query}` not found..."
            return await interaction.send(embed=error_embed, ephemeral=True)

        embed = custom_embed()

        self.channels[interaction.guild.id] = interaction.channel

        if player.current:
            embed.title = "Queue"

            if isinstance(tracks, mafic.Playlist):
                player.queue.extend(tracks.tracks)
                embed.description = f"Added playlist **{tracks.name}** ({len(tracks.tracks)} tracks) to the queue."

            else:
                player.queue.append(tracks[0])
                embed.description = f"Added track **[{tracks[0].title}]({str(tracks[0].uri)})** to the queue."
                embed.add_field(
                    name="Artist:", value=f"**`{tracks[0].author}`**", inline=True
                )
                embed.add_field(
                    name="Duration:",
                    value=f"`{str(datetime.timedelta(seconds=round(tracks[0].length / 1000)))}`",
                    inline=True,
                )
                embed.add_field(
                    name="Message deletion in:", value=f"**`15 seconds`**", inline=True
                )
                embed.set_image(url=tracks[0].artwork_url)

            message = await interaction.followup.send(embed=embed, delete_after=15)
            await message.edit(
                embed=embed, view=NavigationPanelView(self.bot, message.id)
            )

        else:
            if isinstance(tracks, mafic.Playlist):
                player.queue.extend(tracks.tracks[1:])
                await player.play(tracks.tracks[0])

                embed.title = f"Now playing - {tracks.tracks[0].title}"
                embed.description = (
                    f"[{tracks.tracks[0].title}]({str(tracks.tracks[0].uri)})"
                    f"\nAdded playlist {tracks.name} ({len(tracks.tracks) - 1} tracks) to the queue."
                )
                embed.add_field(
                    name="Artist:",
                    value=f"**`{tracks.tracks[0].author}`**",
                    inline=True,
                )
                embed.add_field(
                    name="Duration:",
                    value=f"`{str(datetime.timedelta(seconds=round(tracks.tracks[0].length / 1000)))}`",
                    inline=True,
                )
                embed.set_image(url=tracks.tracks[0].artwork_url)

            else:
                await player.play(tracks[0])

                embed.title = f"Now playing - {tracks[0].title}"
                embed.description = f"[{tracks[0].title}]({str(tracks[0].uri)})"
                embed.add_field(
                    name="Artist:", value=f"**`{tracks[0].author}`**", inline=True
                )
                embed.add_field(
                    name="Duration:",
                    value=f"`{str(datetime.timedelta(seconds=round(tracks[0].length / 1000)))}`",
                    inline=True,
                )
                embed.set_image(url=tracks[0].artwork_url)

            message = await interaction.followup.send(embed=embed)
            await message.edit(
                embed=embed, view=NavigationPanelView(self.bot, message.id)
            )

    @commands.Cog.listener()
    async def on_track_end(self, event: mafic.TrackEndEvent[MusicPlayer]):
        if not event.player.queue or event.player.voice_channel.members == 0:
            if event.player.guild.id in self.channels:
                del self.channels[event.player.guild.id]

            return await event.player.disconnect()

        track = event.player.queue.pop(0)
        await event.player.play(track)

        embed = custom_embed(
            title=f"Now playing - {track.title}",
            description=f"[{track.title}]({str(track.uri)})",
            image=track.artwork_url
        )
        embed.add_field(name="Artist:", value=f"**`{track.author}`**", inline=True)
        embed.add_field(
            name="Duration:",
            value=f"`{str(datetime.timedelta(seconds=round(track.length / 1000)))}`",
            inline=True,
        )

        if channel := self.channels.get(event.player.guild.id):
            message = await channel.send(embed=embed)

            return await message.edit(
                embed=embed, view=NavigationPanelView(self.bot, message_id=message.id)
            )

    @commands.Cog.listener()
    async def on_track_start(self, event: mafic.TrackStartEvent) -> None:
        assert isinstance(event.player, MusicPlayer)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
