from disnake.ext import commands
import disnake
from core.database.repositories.logging import LoggingRepository
from core.database.models.logging import ChannelLogging
from core.misc.embed import custom_embed
from typing import Optional

from core.misc.logging.audit import AuditUtil


class ChannelLoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(ChannelLoggingCog, self).__init__()
        self.bot = bot
        self.logging = LoggingRepository()
        self.audit = AuditUtil(bot)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.TextChannel) -> None:
        result: ChannelLogging = await self.logging.get_channel_logger(
            guild_id=channel.guild.id
        )
        if not result or not result.create_event:
            return

        channel_id: int = result.create_event_channel_id
        try:
            log_channel = self.bot.get_channel(
                channel_id
            ) or await self.bot.fetch_channel(channel_id)
        except (disnake.NotFound, disnake.Forbidden):
            return

        audit: Optional[disnake.AuditLogEntry] = await self.audit._process_audit_log(
            channel.guild, disnake.AuditLogAction.channel_create, duration=3
        )

        embed = custom_embed(
            title="✅ | Channel Created!",
        )
        embed.add_field(
            name="Channel Settings",
            value=(
                f"- Name: `{channel.name}`\n"
                f"- Type: `{channel.type}`\n"
                f"- Topic: `{channel.topic if channel.topic else 'No Topic'}`\n"
                f"- NSFW: `{"✅" if channel.is_nsfw() else "❌"}`\n"
                f"- Created at: {disnake.utils.format_dt(channel.created_at, "R")}\n"
                f"- Creator: `{audit.user.name if audit else 'Unknown'}`"
            ),
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: disnake.TextChannel, after: disnake.TextChannel
    ) -> None:
        if before is after:
            return
        
        result: ChannelLogging = await self.logging.get_channel_logger(
            guild_id=after.guild.id
        )
        if not result or not result.update_event:
            return

        channel_id: int = result.update_event_channel_id
        try:
            log_channel = self.bot.get_channel(
                channel_id
            ) or await self.bot.fetch_channel(channel_id)
        except (disnake.NotFound, disnake.Forbidden):
            return

        audit: Optional[disnake.AuditLogEntry] = await self.audit._process_audit_log(
            after.guild, disnake.AuditLogAction.channel_update, duration=3
        )

        embed = custom_embed(
            title="🔄 | Channel Updated!",
            description=f"- Updater: `{audit.user.name if audit else 'Unknown'}`",
        )

        embed.add_field(
            name="Before Channel Settings",
            value=(
                f"- Name: `{before.name}`\n"
                f"- Type: `{before.type}`\n"
                f"- Topic: `{before.topic if before.topic else 'No Topic'}`\n"
                f"- NSFW: `{"✅" if before.is_nsfw() else "❌"}`\n"
                f"- Created at: {disnake.utils.format_dt(before.created_at, "R")}\n"
            ),
        )

        embed.add_field(
            name="After Channel Settings",
            value=(
                f"- Name: `{after.name}`\n"
                f"- Type: `{after.type}`\n"
                f"- Topic: `{after.topic if after.topic else 'No Topic'}`\n"
                f"- NSFW: `{"✅" if after.is_nsfw() else "❌"}`\n"
                f"- Created at: {disnake.utils.format_dt(after.created_at, "R")}\n"
            ),
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.TextChannel) -> None:
        result: ChannelLogging = await self.logging.get_channel_logger(
            guild_id=channel.guild.id
        )
        if not result or not result.delete_event:
            return

        channel_id: int = result.delete_event_channel_id
        try:
            log_channel = self.bot.get_channel(
                channel_id
            ) or await self.bot.fetch_channel(channel_id)
        except (disnake.NotFound, disnake.Forbidden):
            return

        audit: Optional[disnake.AuditLogEntry] = await self.audit._process_audit_log(
            channel.guild, disnake.AuditLogAction.channel_delete, duration=3
        )

        embed = custom_embed(
            title="❌ | Channel Deleted!",
        )
        embed.add_field(
            name="Channel Settings",
            value=(
                f"- Name: `{channel.name}`\n"
                f"- Type: `{channel.type}`\n"
                f"- Topic: `{channel.topic if channel.topic else 'No Topic'}`\n"
                f"- NSFW: `{"✅" if channel.is_nsfw() else "❌"}`\n"
                f"- Created at: {disnake.utils.format_dt(channel.created_at, "R")}\n"
                f"- Deleter: `{audit.user.name if audit else 'Unknown'}`"
            ),
        )

        await log_channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ChannelLoggingCog(bot))
