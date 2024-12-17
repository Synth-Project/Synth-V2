from disnake.ext import commands
import disnake
from core.database.repositories import LoggingRepository
from core.misc.embed import custom_embed


class MemberEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(MemberEvents, self).__init__()
        self.bot = bot

    async def _get_channel(
        self, guild_id: int, event_type: str
    ) -> tuple[disnake.TextChannel | None, LoggingRepository | None]:
        result = await LoggingRepository.get_member_logger(guild_id=guild_id)
        if not result or not getattr(result, f"{event_type}_event", None):
            return None, None

        try:
            channel_id = getattr(result, f"{event_type}_event_channel_id")
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
            return channel, result
        except (disnake.NotFound, disnake.Forbidden):
            return None, None

    def _create_member_embed(self, member: disnake.Member, title: str) -> disnake.Embed:
        account_age = (disnake.utils.utcnow() - member.created_at).days
        return custom_embed(
            title=title,
            description=f"**Member:** {member.mention}\n"
            f"**Account Created:** {disnake.utils.format_dt(member.created_at, 'R')} ({account_age} days ago)\n"
            f"**Server Member Count:** {member.guild.member_count:,}",
        ).set_thumbnail(url=member.display_avatar.url)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        channel, _ = await self._get_channel(member.guild.id, "join")
        if channel:
            await channel.send(
                embed=self._create_member_embed(
                    member, f"👋 Welcome {member.display_name}!"
                )
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        channel, result = await self._get_channel(member.guild.id, "leave")
        if not channel:
            return

        if result.ban_event:
            async for entry in member.guild.audit_logs(limit=1):
                if (
                    entry.target.id == member.id
                    and entry.action == disnake.AuditLogAction.ban
                    and entry.created_at.timestamp() + 1 >= member.joined_at.timestamp()
                ):
                    return

        await channel.send(
            embed=self._create_member_embed(member, f"👋 Bye {member.display_name}!")
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        channel, _ = await self._get_channel(before.guild.id, "update")
        if not channel:
            return

        field_changes = {
            "Display Name": (before.display_name, after.display_name),
            "Nick": (before.nick, after.nick),
            "Roles": (
                [r.name for r in before.roles],
                [r.name for r in after.roles],
                lambda b, a: f"**Before:** {', '.join(b)}\n**After:** {', '.join(a)}",
            ),
            "Timeout": (
                before.current_timeout,
                after.current_timeout,
                lambda b, a: f"**Before:** {disnake.utils.format_dt(b.timestamp()) if b else 'Not muted'}\n**After:** {disnake.utils.format_dt(a.timestamp()) if a else 'Unmuted'}",
            ),
        }

        embed = custom_embed(
            title="👋 Member Update!", description=f"**Member:** {before.mention}\n"
        ).set_thumbnail(url=before.display_avatar.url)

        for name, values in field_changes.items():
            before_val, after_val, *formatter = values
            if before_val != after_val:
                format_func = (
                    formatter[0]
                    if formatter
                    else lambda b, a: f"**Before:** {b}\n**After:** {a}"
                )
                embed.add_field(
                    name=name, value=format_func(before_val, after_val), inline=False
                )

        if embed.fields:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: disnake.AuditLogEntry):
        handler_name = f"{entry.action.name.lower()}_handler"
        handler = getattr(self, handler_name, lambda e: None)
        await handler(entry)

    async def _handle_ban_event(
        self, entry: disnake.AuditLogEntry, event_type: str, title: str
    ):
        channel, _ = await self._get_channel(entry.guild.id, event_type)
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


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MemberEvents(bot))
