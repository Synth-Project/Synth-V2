from disnake.ext import commands
import disnake
from datetime import datetime

from core.database.models.logging import GuildLogging
from core.database.repositories.logging import LoggingRepository
from core.misc.embed import custom_embed
from core.main.config import settings


class GuildEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(GuildEvents, self).__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild) -> None:
        log_embed = custom_embed(
            title="➕Synth | Joined Guild",
            description=f"**Guild:** `{guild.name}` / `{guild.id}`\n"
            f"**Members:** `{guild.member_count}`\n"
            f"**Joined at:** {disnake.utils.format_dt(datetime.now(), style='f')}\n"
            f"**Created at:** {disnake.utils.format_dt(guild.created_at, style='f')}\n"
            f"**Owner:** `@{guild.owner.name}` / `{guild.owner.id}`",
        )

        channel = self.bot.get_channel(
            settings.BOT_LOGS_ID
        ) or await self.bot.fetch_channel(settings.BOT_LOGS_ID)
        join_embed = (
            custom_embed(
                title="Synth | New Era",
                description=f"""
Hey :wave:. Thanks for adding our multi-functional bot, Synth.

:rocket: Quick start:
1. Set up your bot with `/settings`
2. To get more information about are commands, type `/help <command>`
3. Join our support server — [click](https://discord.gg/7vT3H3tVYp)

Finally, if you have any issues with the bot. You can also join the [Synth Community](https://discord.gg/7vT3H3tVYp) and ask for help.
            """,
            )
            .set_thumbnail(url=self.bot.user.avatar)
            .set_image(
                url="https://cdn.discordapp.com/attachments/1167873742240755843/1168533333010022410/"
                "synthbanner.png?ex=65521c78&is=653fa778&hm=5481d9be9b4f7e39f60d6ac52677de9b44b2236ceaae8b94c5cfd35348f6167a&"
            )
        )

        try:
            await guild.text_channels[0].send(embed=join_embed)
        except (disnake.HTTPException, disnake.Forbidden, TypeError, ValueError):
            await guild.system_channel.send(embed=join_embed)
        await channel.send(embed=log_embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild) -> None:
        log_embed = custom_embed(
            title="➖Synth | Left Guild",
            description=f"**Guild:** `{guild.name}` / `{guild.id}`\n"
            f"**Members:** `{guild.member_count}`\n"
            f"**Created at:** {disnake.utils.format_dt(guild.created_at, style='f')}\n"
            f"**Owner:** `@{guild.owner.name}` / `{guild.owner.id}`",
        )
        channel = self.bot.get_channel(
            settings.BOT_LOGS_ID
        ) or await self.bot.fetch_channel(settings.BOT_LOGS_ID)
        await channel.send(embed=log_embed)

    @commands.Cog.listener()
    async def on_guild_update(
        self, before: disnake.Guild, after: disnake.Guild
    ) -> None:
        if before == after:
            return

        result: GuildLogging = await LoggingRepository.get_guild_logger(
            guild_id=before.id
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

        embed = custom_embed(
            title="👋 Guild Update!", description=f"**Guild:** {before.name}\n"
        )
        embed.set_thumbnail(url=before.icon)

        field_changes = {
            "- Name": (before.name, after.name),
            "- Description": (before.description, after.description),
            "- Icon": (before.icon, after.icon),
            "- Banner": (before.banner, after.banner),
            "- Splash": (before.splash, after.splash),
            "- Owner": (before.owner_id, after.owner_id),
            "- Verification Level": (before.verification_level, after.verification_level),
            "- NSFW Level": (before.nsfw_level, after.nsfw_level),
            "- Region": (before.region, after.region),
            "- AFK Channel": (before.afk_channel, after.afk_channel),
        }

        for name, (before_val, after_val) in field_changes.items():
            if before_val != after_val:
                embed.add_field(
                    name=name,
                    value=f"**Before:** __{before_val}__\n**After:** __{after_val}__",
                    inline=False,
                )

        if embed.fields:
            await channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(GuildEvents(bot))
