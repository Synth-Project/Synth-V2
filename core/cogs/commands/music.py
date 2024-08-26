import datetime
from collections import defaultdict
from typing import Dict, List, cast

import mafic
import wavelink

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

        bot.loop.create_task(self.add_nodes())

    async def add_nodes(self) -> None:
        # await wavelink.Pool.create_node(
        #     bot=self.bot,
        #     host="localhost",
        #     port=2333,
        #     password="youshallnotpass",
        # )
        nodes = [wavelink.Node(uri="http://localhost:2333", password="youshallnotpass")]

        # cache_capacity is EXPERIMENTAL. Turn it off by passing None
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print("Wavelink Node connected: %r | Resumed: %s", payload.node, payload.resumed)

    @commands.slash_command(description="Search and play music from Spotify")
    async def play(self, interaction: disnake.MessageCommandInteraction, *, query: str):
        if not interaction.guild:
            return

        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

        try:
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)  # type: ignore
        except AttributeError:
            await interaction.send("Please join a voice channel first before using this command.")
            return
        except disnake.ClientException:
            await interaction.send("I was unable to join this voice channel. Please try again.")
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
            await interaction.send(f"You can only play songs in {player.home.mention}, as the player has already started there.")
            return

        # This will handle fetching Tracks and Playlists...
        # Seed the doc strings for more information on this method...
        # If spotify is enabled via LavaSrc, this will automatically fetch Spotify tracks if you pass a URL...
        # Defaults to YouTube for non URL based queries...
        tracks: wavelink.Search = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTube)
        if not tracks:
            await interaction.send(f"{interaction.user.mention} - Could not find any tracks with that query. Please try again.")
            return

        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            added: int = await player.queue.put_wait(tracks)
            await interaction.send(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await interaction.send(f"Added **`{track}`** to the queue.")

        if not player.playing:
            # Play now since we aren't playing anything...
            await player.play(player.queue.get(), volume=30)

        # Optionally delete the invokers message...
        try:
            await interaction.original_response.delete()
        except disnake.HTTPException:
            pass
     
    # редачити:
    # wavelink.player (весь діскорд на діснейк)  + убираєш анотацію якорї в діснйеку немає
    # wavelink.node (весь діскорд на діснейк) 

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
