from datetime import timedelta

import wavelink
from disnake.ext import commands

from core import logger
from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed
from core.misc.music.views.panel import NavigationPanel


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
        message = payload.player.message  # type: ignore

        if (
            payload.player.queue.mode == wavelink.QueueMode.loop
            and original != payload.player.current
        ):
            await payload.player.play(payload.original, add_history=False)

        requestor = getattr(track.extras, "requested_by", None)
        if requestor:
            requestor = await self.bot.get_or_fetch_user(requestor)

        embed = CustomEmbed(
            author=requestor,
            title="Now playing",
            description=f"[{track.title}]({str(track.uri)})",
            footer_text=f"Volume: {payload.player.volume}% // Synth Music 2024",
        ).get_embed()
        embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
        embed.add_field(
            name="Duration:",
            value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
            inline=True,
        )

        if original and original.recommended:
            embed.set_footer(text=f"Auto recommended // Synth Music 2024")
        elif payload.player.queue.mode == wavelink.QueueMode.loop:
            embed.set_footer(text="This track was looped // Synth Music 2024")

        embed.set_image(url=track.artwork if track.artwork else None)
        history_exists = payload.player.queue.history.count > 0

        await message.edit(  # type: ignore
            embed=embed,
            view=NavigationPanel(
                self.bot,
                message.id,
                history_exists=history_exists,
                player=payload.player,
                interaction=message,
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
        else:
            old_track = payload.original
            player.queue.history.put_at(0, old_track)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        await player.disconnect()
        embed = CustomEmbed(
            title="Disconnected from voice channel",
            color=BasicColors.SUCCESS,
            description="Disconnected from voice channel due to inactivity",
        ).get_embed()

        await player.message.reply(embed=embed)  # type: ignore


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MusicEvent(bot))
