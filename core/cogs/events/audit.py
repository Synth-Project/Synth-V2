from disnake.ext import commands
import disnake
from core.database.repositories import LoggingRepository
from core.misc.embed import custom_embed


class AuditActionEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(AuditActionEvents, self).__init__()
        self.bot = bot
        self.logging = LoggingRepository()
        self.handlers = {
            disnake.AuditLogAction.ban: self.ban_handler,
            disnake.AuditLogAction.unban: self.unban_handler,
            disnake.AuditLogAction.message_delete: None,
            disnake.AuditLogAction.message_bulk_delete: None,
            disnake.AuditLogAction.role_create: None,
        }

    async def _handle_ban_event(
        self, entry: disnake.AuditLogEntry, event_type: str, title: str
    ):
        channel, _ = await self.logging.get_channel(
            self.bot, entry.guild.id, event_type
        )
        if not channel:
            return

        target = self.bot.get_user(entry.target.id) or await self.bot.fetch_user(
            entry.target.id
        )
        embed = custom_embed(
            title=title,
            description=f"{target.mention} was {event_type}ned by {entry.user.mention}",
        ).set_thumbnail(url=entry.target.display_avatar.url)

        if entry.reason and event_type == "ban":
            embed.add_field(name="Reason", value=entry.reason, inline=False)

        await channel.send(embed=embed)

    async def ban_handler(self, entry: disnake.AuditLogEntry):
        await self._handle_ban_event(entry, "ban", "👋 Ban Event!")

    async def unban_handler(self, entry: disnake.AuditLogEntry):
        await self._handle_ban_event(entry, "unban", "👋 Unban Event!")

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: disnake.AuditLogEntry):
        # # async def handle():  # не, а ну ща попроубем так
            # pass
        handler_name = f"{entry.action.name.lower()}_handler"
        handler = getattr(self, handler_name)

        if handler is not None:
            await handler(entry)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AuditActionEvents(bot))
