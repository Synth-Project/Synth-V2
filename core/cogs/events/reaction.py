from disnake.ext import commands
import disnake
from core.database.repositories.logging import LoggingRepository
from core.database.models.logging import ReactionLogging
from core.misc.embed import custom_embed
import datetime
from typing import Optional, Union

from core.misc.logging.audit import AuditUtil


class ReactionLoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(ReactionLoggingCog, self).__init__()
        self.bot = bot
        self.logging = LoggingRepository()
        self.audit = AuditUtil(bot)

    @commands.Cog.listener()
    async def on_reaction_add(
        self, reaction: disnake.Reaction, user: Union[disnake.Member, disnake.User]
    ) -> None:
        result: ReactionLogging = await self.logging.get_reaction_logger(
            guild_id=reaction.message.guild.id
        )
        if not result or not result.remove_event:
            return

        channel_id: int = result.remove_event_channel_id
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
        except (disnake.NotFound, disnake.Forbidden):
            return

        embed = custom_embed(
            title="✅ | Reaction Added!",
        )
        embed.add_field(
            name="Reaction Settings",
            value=(
                f"- Message ID: `{reaction.message.id}`\n"
                f"- User ID: `{user.id}`\n"
                f"- Reaction: `{reaction.emoji}`\n"
                f"- Added at: {disnake.utils.format_dt(datetime.datetime.now(), 'R')}\n"
                f"- Adder: `{user.name if user else 'Unknown'}`"
            ),
            inline=False,
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_remove(
        self, reaction: disnake.Reaction, user: Union[disnake.Member, disnake.User]
    ) -> None:
        result: ReactionLogging = await self.logging.get_reaction_logger(
            guild_id=reaction.message.guild.id
        )
        if not result or not result.remove_event:
            return

        channel_id: int = result.remove_event_channel_id
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
        except (disnake.NotFound, disnake.Forbidden):
            return

        embed = custom_embed(
            title="❌ | Reaction Removed!",
        )
        embed.add_field(
            name="Reaction Settings",
            value=(
                f"- Message ID: `{reaction.message.id}`\n"
                f"- User ID: `{user.id}`\n"
                f"- Reaction: `{reaction.emoji}`\n"
                f"- Removed at: {disnake.utils.format_dt(datetime.datetime.now(), 'R')}\n"
                f"- Remover: `{user.name if user else 'Unknown'}`"
            ),
            inline=False,
        )

        await channel.send(embed=embed)

    # @commands.Cog.listener()
    # async def on_reaction_clear(self, message: disnake.Message, reactions: list[disnake.Reaction]) -> None:
    #     result: ReactionLogging = await self.logging.get_reaction_logger(guild_id=message.guild.id)
    #     if not result or not result.clear_event:
    #         return

    #     channel_id: int = result.clear_event_channel_id
    #     try:
    #         channel = await self.bot.get_channel(channel_id)
    #     except (disnake.NotFound, disnake.Forbidden):
    #         return

    #     embed = custom_embed(
    #         title="❌ | Reaction Cleared!",
    #     )
    #     embed.add_field(
    #         name = "Reaction Settings",
    #         value = (
    #             f"Message ID: `{message.id}`\n"
    #             f"Channel ID: `{message.channel.id}`\n"
    #             f"Message Author ID: `{message.author.id}`\n"
    #             f"Message Author: `{message.author.name if message.author else 'Unknown'}`\n"
    #         )
    #     ) TODO: Give more information about reactions ? But idk how

    #     await channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ReactionLoggingCog(bot))
