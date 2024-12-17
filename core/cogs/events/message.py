import disnake
from disnake.ext import commands
from loguru import logger
from typing import Optional, Dict, List

from core.database.models.logging import MessageLogging
from core.database.repositories.logging import LoggingRepository


class MessageEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.cache_audit_log: Dict[str, List[disnake.AuditLogEntry]] = {}
        self.logger = logger.bind(source=self.__class__.__name__)

    async def cog_load(self) -> None:
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            await self._init_audit_log_cache(guild)

    async def _init_audit_log_cache(self, guild: disnake.Guild) -> None:
        guild_id = str(guild.id)
        self.cache_audit_log[guild_id] = []

        delete_actions = {
            disnake.AuditLogAction.message_delete,
            disnake.AuditLogAction.message_bulk_delete,
        }

        async for entry in guild.audit_logs(limit=10):
            if entry.action in delete_actions:
                self.cache_audit_log[guild_id].append(entry)

        self.logger.info(f"Cached last 10 audit logs for {guild.name} ({guild.id})")

    async def _process_audit_log(
        self,
        guild: disnake.Guild,
        action: disnake.AuditLogAction,
        message_author_id: Optional[int] = None,
    ) -> Optional[disnake.AuditLogEntry]:
        """Process audit log entries and update cache."""
        guild_id = str(guild.id)
        async for entry in guild.audit_logs(limit=1, action=action):
            cache = self.cache_audit_log.get(guild_id, [])

            cached_entry = next((log for log in cache if log.id == entry.id), None)

            is_new = cached_entry is None
            is_updated = cached_entry and cached_entry.extra.count < entry.extra.count

            if is_new or is_updated:
                self.cache_audit_log[guild_id] = [
                    log for log in cache if log.id != entry.id
                ]
                self.cache_audit_log[guild_id].append(entry)

                if not message_author_id or entry.target.id == message_author_id:
                    return entry

        return None

    def _log_deletion(self, content: str, **kwargs) -> None:
        """Centralized logging for message deletions."""
        self.logger.info(content, **kwargs)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if not message.guild:
            return

        result: MessageLogging = await LoggingRepository.get_message_logger(
            guild_id=message.guild.id
        )
        if not result or not result.delete_event:
            return

        entry = await self._process_audit_log(
            message.guild, disnake.AuditLogAction.message_delete, message.author.id
        )

        if entry and entry.user.id != message.author.id:
            self._log_deletion(
                "Message deleted by moderator | "
                f"Mod: {entry.user} ({entry.user.id}) | "
                f"Author: {message.author} ({message.author.id}) | "
                f"Content: {message.content}"
            )
        else:
            self._log_deletion(
                f"Message self-deleted by {message.author} ({message.author.id}) | "
                f"Content: {message.content}"
            )

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(
        self, payload: disnake.RawBulkMessageDeleteEvent
    ) -> None:
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        entry = await self._process_audit_log(
            guild, disnake.AuditLogAction.message_bulk_delete
        )

        if entry:
            self._log_deletion(
                f"Bulk deletion of {len(payload.message_ids)} messages | "
                f"Mod: {entry.user} ({entry.user.id}) | "
                f"Channel: {payload.channel_id}"
            )
        else:
            self._log_deletion(
                f"Bulk deletion of {len(payload.message_ids)} messages | "
                f"Channel: {payload.channel_id}"
            )

    @commands.Cog.listener()
    async def on_raw_message_delete(
        self, payload: disnake.RawMessageDeleteEvent
    ) -> None:
        if getattr(payload, "cached_message", None):
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        entry = await self._process_audit_log(
            guild, disnake.AuditLogAction.message_delete
        )

        if entry:
            self._log_deletion(
                f"Uncached message deletion | "
                f"Message ID: {payload.message_id} | "
                f"Mod: {entry.user} ({entry.user.id}) | "
                f"Channel: {payload.channel_id}"
            )
        else:
            self._log_deletion(
                f"Uncached message deletion | "
                f"Message ID: {payload.message_id} | "
                f"Channel: {payload.channel_id}"
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MessageEvents(bot))
