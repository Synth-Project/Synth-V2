import datetime
from typing import Optional
import disnake
from disnake.ext import commands

from core.misc.embed import custom_embed

class AuditUtil:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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