import importlib

import wavelink
from disnake.ext import commands

from core import logger
from core.misc.embed import CustomEmbed
from core.misc.misc import mention_slash
from core.misc.music.views.panel import NavigationPanel


class MusicEvent(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super(MusicEvent, self).__init__()
        self.bot = bot

        self.bot.loop.create_task(self.connect_nodes())
        self.logger = logger.bind(source=self.__class__.__module__)

        self.functions = getattr(
            importlib.import_module("core.misc.music.functions"), "MusicFunctions"
        )

    async def connect_nodes(self) -> None:
        nodes = [wavelink.Node(uri="http://0.0.0.0:2333", password="weever_gay")]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, _: wavelink.NodeReadyEventPayload) -> None:
        self.logger.info("[+] Wavelink Node ready")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        original = payload.original
        track = payload.track
        message = payload.player.main_message
        # message = payload.player.message  # type: ignore

        print("event")

        if (
            payload.player.queue.mode == wavelink.QueueMode.loop
            and original != payload.player.current
        ):
            await payload.player.play(payload.original, add_history=False)

        embed = await self.functions.music_embed(message, track)

        embed.set_image(url=track.artwork if track.artwork else None)
        queue = (
            payload.player.queue
            if not payload.player.queue.is_empty
            else (
                payload.player.auto_queue
                if payload.player.autoplay == wavelink.AutoPlayMode.enabled
                else payload.player.queue
            )
        )
        history_exists = queue.history.count > 0

        await message.edit(  # type: ignore
            content=None,
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
        elif not player.current and not player.playing:
            old_track = payload.original
            player.queue.history.put_at(0, old_track)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        await player.disconnect()

        embed = CustomEmbed(
            title="<:disconnect:1279835624257486868> Disconnected",
            description=(
                f"I've left the {player.channel.mention} due to inactivity. \n"
                f"If you will need me again, use the {mention_slash(player.guild, 'player play')} command."
            ),
        ).get_embed()

        await player.main_message.reply(embed=embed)
        await player.main_message.delete()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MusicEvent(bot))
