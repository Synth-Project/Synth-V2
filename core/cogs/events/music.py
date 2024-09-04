from datetime import timedelta
from disnake.ext import commands
import wavelink

from core import logger
from core.misc.embed import custom_embed
from core.misc.views.music.panel import NavigationPanel


class MusicEvent(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super(MusicEvent, self).__init__()
        self.bot = bot

        self.bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self) -> None:
        nodes = [wavelink.Node(uri="http://localhost:2333", password="weever_gay")]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, _: wavelink.NodeReadyEventPayload) -> None:
        logger.info("[+] Wavelink Node ready")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        original = payload.original
        track = payload.track

        if hasattr(payload.player, "first_play") and payload.player.first_play:
            payload.player.first_play = False
            return

        if (
            payload.player.queue.mode == wavelink.QueueMode.loop
            and original != payload.player.current
        ):
            await payload.player.play(payload.original, add_history=False)

        embed = custom_embed()
        embed.title = f"Now playing - {track.title}"
        embed.description = f"[{track.title}]({str(track.uri)})"
        embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
        embed.add_field(
            name="Duration:",
            value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
            inline=True,
        )

        if original and original.recommended:
            embed.set_footer(text=f"This track was recommended via {track.source}")
        elif payload.player.queue.mode == wavelink.QueueMode.loop:
            embed.set_footer(text="This track was looped")

        embed.set_image(url=track.artwork if track.artwork else None)

        message = await payload.player.interaction.followup.send(embed=embed)

        history_exists = payload.player.queue.history.count > 0

        await message.edit(
            embed=embed,
            view=NavigationPanel(
                self.bot,
                message.id,
                history_exists=history_exists,
                player=payload.player,
            ),
        )

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload: wavelink.TrackEndEventPayload
    ) -> None:
        player = payload.player

        assert player

        if not player.queue.is_empty:
            new_track = player.queue.get()
            await player.play(new_track, add_history=False)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MusicEvent(bot))
