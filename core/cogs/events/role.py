from disnake.ext import commands
import disnake
from core.database.repositories.logging import LoggingRepository
from core.database.models.logging import RoleLogging
from core.misc.embed import custom_embed
import datetime
from typing import Optional


class RoleLoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(RoleLoggingCog, self).__init__()
        self.bot = bot
        self.logging = LoggingRepository()

    async def _process_audit_log(
        self,
        guild: disnake.Guild,
        action: disnake.AuditLogAction,
        duration: int = 3,
    ) -> Optional[disnake.AuditLogEntry]:
        created_at = datetime.datetime.now(
            tz=datetime.timezone.utc
        ) - datetime.timedelta(seconds=duration)
        async for entry in guild.audit_logs(limit=1, action=action):
            if entry.created_at.timestamp() >= created_at.timestamp():
                return entry

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role) -> None:
        result: RoleLogging = await self.logging.get_role_logger(
            guild_id=role.guild.id
        )
        if not result or not result.create_event:
            return

        channel_id: int = result.create_event_channel_id
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
        except (disnake.NotFound, disnake.Forbidden):
            return

        audit: Optional[disnake.AuditLogEntry] = await self._process_audit_log(
            role.guild, disnake.AuditLogAction.role_create, duration=3
        )

        # эт тот кто создал роль !!!! (похожее)
        # if entry and entry.user.id != message.author.id:
        #     self._log_deletion(
        #         "Message deleted by moderator | "
        #         f"Mod: {entry.user} ({entry.user.id}) | "
        #         f"Author: {message.author} ({message.author.id}) | "
        #         f"Content: {message.content}"
        #     )
        #     # await
        # else:
        #     self._log_deletion(
        #         f"Message self-deleted by {message.author} ({message.author.id}) | "
        #         f"Content: {message.content}"
        #     )

        embed = custom_embed(
            title="Role Created!",
        )
        embed.add_field(
            name = "Role Settings",
            value = (
                f"Name: {role.name}\n"
                f"Mentionable: {"✅" if role.mentionable else "❌"}\n"
                f"Creator: {audit.user.name if audit else "Unknown"}" # попробуй ща єт и да, я спать
            )
        )

        await channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(RoleLoggingCog(bot))
