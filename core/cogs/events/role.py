from disnake.ext import commands
import disnake
from core.database.repositories.logging import LoggingRepository
from core.database.models.logging import RoleLogging
from core.misc.embed import custom_embed
import datetime
from typing import Optional

from core.misc.logging.audit import AuditUtil


class RoleLoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(RoleLoggingCog, self).__init__()
        self.bot = bot
        self.logging = LoggingRepository()
        self.audit = AuditUtil(bot)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role) -> None:
        result: RoleLogging = await self.logging.get_role_logger(guild_id=role.guild.id)
        if not result or not result.create_event:
            return

        channel_id: int = result.create_event_channel_id
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
        except (disnake.NotFound, disnake.Forbidden):
            return

        audit: Optional[disnake.AuditLogEntry] = await self.audit._process_audit_log(
            role.guild, disnake.AuditLogAction.role_create, duration=3
        )

        embed = custom_embed(
            title="✅ | Role Created!",
        )
        embed.add_field(
            name="Role Settings",
            value=(
                f"- Name: {role.name}\n"
                f"- Color: `{role.color}`\n"
                f"- Mentionable: `{"✅" if role.mentionable else "❌"}`\n"
                f"- Position: `{role.position}`\n"
                f"- Creator: {audit.user.name if audit else "Unknown"}"
            ),
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: disnake.Role) -> None:
        result: RoleLogging = await self.logging.get_role_logger(guild_id=role.guild.id)
        if not result or not result.delete_event:
            return

        channel_id: int = result.delete_event_channel_id
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
        except (disnake.NotFound, disnake.Forbidden):
            return

        audit: Optional[disnake.AuditLogEntry] = await self.audit._process_audit_log(
            role.guild, disnake.AuditLogAction.role_delete, duration=3
        )

        embed = custom_embed(
            title="❌ | Role Deleted!",
        )
        embed.add_field(
            name="Role Settings",
            value=(
                f"- Name: `{role.name}`\n"
                f"- Color: `{role.color}`\n"
                f"- Mentionable: `{"✅" if role.mentionable else "❌"}`\n"
                f"- Position: `{role.position}`\n"
                f"- Created at: {disnake.utils.format_dt(role.created_at, "R")}\n"
                f"- Deleter: `{audit.user.name if audit else 'Unknown'}`\n"
            ),
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(
        self, before: disnake.Role, after: disnake.Role
    ) -> None:
        if before == after:
            return
        
        result: RoleLogging = await self.logging.get_role_logger(
            guild_id=after.guild.id
        )
        if not result or not result.update_event:
            return

        channel_id: int = result.update_event_channel_id
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
        except (disnake.NotFound, disnake.Forbidden):
            return

        audit: Optional[disnake.AuditLogEntry] = await self.audit._process_audit_log(
            after.guild, disnake.AuditLogAction.role_update, duration=3
        )

        embed = custom_embed(
            title="ℹ️ | Role Updated!",
            description=f"- Updater: `{audit.user.name if audit else 'Unknown'}`",
        )
        embed.add_field(
            name="Before Role Settings",
            value=(
                f"- Name: `{before.name}`\n"
                f"- Color: `{before.color}`\n"
                f"- Mentionable: `{"✅" if before.mentionable else "❌"}`\n"
                f"- Position: `{before.position}`\n"
                f"- Created at: {disnake.utils.format_dt(before.created_at, "R")}\n"
            ),
        )

        embed.add_field(
            name="After Role Settings",
            value=(
                f"- Name: `{after.name}`\n"
                f"- Color: `{after.color}`\n"
                f"- Mentionable: `{"✅" if after.mentionable else "❌"}`\n"
                f"- Position: `{after.position}`\n"
                f"- Created at: {disnake.utils.format_dt(after.created_at, "R")}\n"
            ),
        )
        await channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(RoleLoggingCog(bot))
