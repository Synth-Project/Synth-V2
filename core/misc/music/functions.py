from dataclasses import dataclass
from datetime import timedelta

import disnake
from disnake.ext.commands import Bot
import wavelink

from core.main.main import bot
from core.misc.embed import CustomEmbed
from core.misc.color import BasicColors
from core.misc.music.views.panel import NavigationPanel


@dataclass
class MusicFunctions:
    @staticmethod
    async def music_embed(track: wavelink.Playable) -> disnake.Embed:
        embed = CustomEmbed(title=track.title, image=track.artwork).get_embed()
        embed.url = str(track.uri)

        embed.add_field(name="Artist:", value=f"`{track.author}`", inline=True)
        embed.add_field(
            name="Duration:",
            value=f"`{str(timedelta(seconds=round(track.length / 1000)))}`",
            inline=True,
        )

        return embed

    async def play_track(
        self,
        bot: Bot,
        interaction: disnake.Interaction,
        player: wavelink.Player,
        embed: disnake.Embed,
        track: wavelink.Playable,
        volume: int,
    ) -> None:
        if not player.playing:
            if not player.current:
                await player.set_volume(min(100, max(1, volume)))
            embed = await self.music_embed(track)
            message = await interaction.channel.send(content=None, embed=embed)
            await interaction.delete_original_response(delay=2)

            track = player.queue.get()

            setattr(player, "message", message)
            player.inactive_timeout = 300

            await player.play(track, add_history=False)

        else:
            await interaction.edit_original_response(content=None, embed=embed)
            await interaction.delete_original_response(delay=5)

        await player.message.edit(  # type: ignore
            view=NavigationPanel(
                bot,
                (await interaction.original_response()).id,
                history_exists=False,
                player=player,
                interaction=interaction,
            )
        )

    @staticmethod
    async def skip_track(
        player: wavelink.Player, interaction: disnake.ApplicationCommandInteraction
    ) -> None:
        embed = CustomEmbed(
            author=interaction.user,  # type: ignore
            title="Track skipped",
            description=(
                f"Skipped the **[{player.current.title}]({str(player.current.uri)})**.\n"
                f"Now playing: **[{player.queue[0].title}]({str(player.queue[0].uri)})**."
            ),
            color=BasicColors.SUCCESS,
        ).get_embed()

        await interaction.delete_original_response()  # TODO: В ідеалі нам тут нічого відповідати не треба, бо це калл, але я хз, башка не робить.
        await player.message.reply(embed=embed)  # type: ignore
        await player.skip()

    @staticmethod
    async def set_volume(player: wavelink.Player, volume: int) -> None:
        embed: disnake.Embed = player.message.embeds[0]  # type: ignore
        embed.set_footer(
            text=f"Volume: {volume}% // Synth Music 2024", icon_url=bot.get_avatar()
        )
        await player.message.edit(embed=embed)  # type: ignore
        await player.set_volume(min(100, max(1, volume)))
