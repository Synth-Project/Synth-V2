from disnake.ext import commands
import disnake
from core.database.repositories import LoggingRepository
from core.misc.logging.audit import AuditUtil


class AuditActionEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(AuditActionEvents, self).__init__()
        self.bot = bot
        self.logging = LoggingRepository()
        self.handlers = {
            disnake.AuditLogAction.ban: self.ban_handler,
            disnake.AuditLogAction.unban: self.unban_handler,
            # disnake.AuditLogAction.message_delete: None,
            # disnake.AuditLogAction.message_bulk_delete: None,
            # disnake.AuditLogAction.role_create: None,
            # disnake.AuditLogAction.role_update: None,
            # disnake.AuditLogAction.role_delete: None,
        }
        self.audit = AuditUtil(bot)

    async def ban_handler(self, entry: disnake.AuditLogEntry):
        await self.audit._handle_ban_event(entry, "ban", "👋 Ban Event!")

    async def unban_handler(self, entry: disnake.AuditLogEntry):
        await self.audit._handle_ban_event(entry, "unban", "👋 Unban Event!")

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: disnake.AuditLogEntry):
        if entry.action not in self.handlers:
            return
        handler_name = f"{entry.action.name.lower()}_handler"
        handler = getattr(self.audit, handler_name)

        if handler is not None:
            await handler(entry)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AuditActionEvents(bot))
