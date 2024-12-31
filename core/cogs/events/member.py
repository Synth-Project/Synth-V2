from disnake.ext import commands
import disnake
from core.database.repositories import LoggingRepository
from core.misc.embed import custom_embed


class MemberEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(MemberEvents, self).__init__()
        self.bot = bot
        self.logging = LoggingRepository()

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        channel, _ = await self.logging.get_channel(self.bot, member.guild.id, "join")
        if channel:
            await channel.send(
                embed=self._create_member_embed(
                    member, f"👋 Welcome {member.display_name}!"
                )
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        channel, result = await self.logging.get_channel(
            self.bot, member.guild.id, "leave"
        )
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
        if before is after:
            return
        channel, _ = await self.logging.get_channel(self.bot, before.guild.id, "update")
        if not channel:
            return

        field_changes = {
            "- Display Name": (before.display_name, after.display_name),
            "- Nick": (before.nick, after.nick),
            "- Roles": (
                [r.name for r in before.roles],
                [r.name for r in after.roles],
                lambda b, a: f"**Before:** {', '.join(b)}\n**After:** {', '.join(a)}",
            ),
            "- Timeout": (
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
                    else lambda b, a: f"**Before:** __{b}__\n**After:** __{a}__"
                )
                embed.add_field(
                    name=name, value=format_func(before_val, after_val), inline=False
                )

        if embed.fields:
            await channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MemberEvents(bot))
