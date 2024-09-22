import importlib
from typing import cast

import disnake
import wavelink

from core.misc.embed import CustomEmbed


class MusicError:
    def __init__(self) -> None:
        pass

    @staticmethod
    async def check_basic(
        interaction: disnake.ApplicationCommandInteraction, query: str = None
    ) -> None:
        player: wavelink.Player = (
            interaction.guild.voice_client
            or await interaction.author.voice.channel.connect(cls=wavelink.Player)
        )

        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if query and query.startswith("❌"):
            error_embed.title = query
            return await interaction.send(embed=error_embed, ephemeral=True)

        elif not player:
            error_embed.title = (
                "<:crossmark:1282338837456224394> | You are not in a voice channel"
            )
            return await interaction.send(embed=error_embed, ephemeral=True)

        return

    @staticmethod
    async def check_queue(interaction: disnake.ApplicationCommandInteraction) -> None:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if not player.queue.is_empty and not player.auto_queue.is_empty:
            error_embed.title = "<:crossmark:1282338837456224394> | Your queue is empty"
            return await interaction.send(embed=error_embed, ephemeral=True)

        return

    @staticmethod
    async def check_error_volume(
        interaction: disnake.Interaction, volume: int
    ) -> disnake.Embed:
        music_functions = getattr(
            importlib.import_module("core.misc.music.functions"), "MusicFunctions"
        )
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if player.volume == volume:
            embed = CustomEmbed.error_embed(
                author=interaction.user,
                title=f"<:crossmark:1282338837456224394> Cannot set the same volume ({volume}%)",
            ).get_embed()

        else:
            embed = CustomEmbed(
                author=interaction.user,
                title=f"<:checkmark:1282338829486788670> Set volume to {volume}",
            ).get_embed()

            await music_functions.set_volume(player, volume)

        return embed
