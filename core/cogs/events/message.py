import datetime
import disnake
from disnake.ext import commands

from core.database.models.logging import MessageLogging
from core.database.repositories.logging import LoggingRepository
from core.misc.embed import custom_embed
from core.misc.logging.audit import AuditUtil

import io


class MessageEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.audit = AuditUtil(bot)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if not message.guild:
            return

        result: MessageLogging = await LoggingRepository.get_message_logger(
            guild_id=message.guild.id
        )
        if not result or not result.delete_event:
            return

        try:
            channel = self.bot.get_channel(
                result.delete_event_channel_id
            ) or await self.bot.fetch_channel(result.delete_event_channel_id)
        except (disnake.NotFound, disnake.Forbidden):
            return

        entry = await self.audit._process_audit_log(
            message.guild, disnake.AuditLogAction.message_delete, 3
        )

        embed = custom_embed(
            title="❌ | Message Deleted!",
        )
        if entry and entry.user.id != message.author.id:
            embed.add_field(
                name="Message Settings",
                value=(
                    f"- Message ID: `{message.id}`\n"
                    f"- Author ID: `{message.author.id}`\n"
                    f"- Author: `{message.author}`\n"
                    f"- Channel: {message.channel.mention}\n"
                    f"- Channel ID: `{message.channel.id}`\n"
                    f"- Deleted at: {disnake.utils.format_dt(datetime.datetime.now(), 'R')}\n"
                    f"- Deleter: `{entry.user}`\n"
                    f"- Content:\n```{"Content is too long, see attached content.txt" if len(message.content) > 1024 else message.content}```\n"
                ),
            )
        else:
            embed.add_field(
                name="Message Settings",
                value=(
                    f"- Message ID: `{message.id}`\n"
                    f"- Author ID: `{message.author.id}`\n"
                    f"- Author: `{message.author}`\n"
                    f"- Channel: {message.channel.mention}\n"
                    f"- Channel ID: `{message.channel.id}`\n"
                    f"- Deleted at: {disnake.utils.format_dt(datetime.datetime.now(), 'R')}\n"
                    f"- Content:\n```{"Content is too long, see attached content.txt" if len(message.content) > 1024 else message.content}```\n"
                ),
            )

        files = []
        embed.add_field(
            name="Additional information",
            value="- No information available",
            inline=False,
        )
        additional_field_index = next(
            index
            for index, field in enumerate(embed.fields)
            if field.name == "Additional information"
        )

        if message.attachments:
            for attachment in message.attachments:
                if len(files) >= (9 if len(message.content) > 1024 else 10):
                    break
                if attachment.size < 10_485_760:  # Size limit: 10 MB
                    files.append(await attachment.to_file())

            embed.set_field_at(
                additional_field_index,
                name="Additional information",
                value=f"Number of media files: `{len(files)}`",
                inline=False,
            )

        if len(message.content) >= 1024:
            content_file = io.StringIO(message.content)
            files.append(disnake.File(content_file, filename="content.txt"))
            embed.add_field(
                name="Content",
                value="Content too long, see attached content.txt",
            )

        await channel.send(embed=embed, files=files)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(
        self, payload: disnake.RawBulkMessageDeleteEvent
    ) -> None:
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        entry = await self.audit._process_audit_log(
            guild, disnake.AuditLogAction.message_bulk_delete, 3
        )

        try:
            channel = self.bot.get_channel(
                payload.channel_id
            ) or await self.bot.fetch_channel(payload.channel_id)
        except (disnake.NotFound, disnake.Forbidden):
            return

        embed = custom_embed(
            title="❌ | Bulk Message Deleted!",
        )

        if entry:
            embed.add_field(
                name="Delete Info",
                value=(
                    f"- Deleted: `{len(payload.message_ids)}` messages\n"
                    f"- Mod: `{entry.user}` (`{entry.user.id}`)\n"
                    f"- Channel: {payload.channel_id}\n"
                ),
            )
        else:
            embed.add_field(
                name="Delete Info",
                value=(
                    f"- Deleted: `{len(payload.message_ids)}` messages\n"
                    f"- Channel: `{payload.channel_id}`\n"
                ),
            )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: disnake.Message, after: disnake.Message
    ) -> None:
        if before is after or after.author.bot:
            return

        result: MessageLogging = await LoggingRepository.get_message_logger(
            guild_id=before.guild.id
        )
        if not result or not result.edit_event:
            return

        try:
            channel = self.bot.get_channel(
                result.edit_event_channel_id
            ) or await self.bot.fetch_channel(result.edit_event_channel_id)
        except (disnake.NotFound, disnake.Forbidden):
            return

        embed = custom_embed(
            title="📝 | Message Edited!",
            description=(
                f"- Message ID: `{after.id}` (**[jump to message]({after.jump_url})**)\n"
                f"- Author ID: `{after.author.id}`\n"
                f"- Author: `{after.author}`\n"
                f"- Sent at: {disnake.utils.format_dt(before.created_at, 'R')}\n"
                f"- Edited at: {disnake.utils.format_dt(after.edited_at, 'R')}"
            ),
        )

        files = []
        for content, name, filename in [
            (before.content, "Before Edit", "before_edit.txt"),
            (after.content, "After Edit", "after_edit.txt"),
        ]:
            if len(content) >= 1024:
                content_file = io.StringIO(content)
                files.append(disnake.File(content_file, filename=filename))
                embed.add_field(
                    name=name, value=f"Content too long, see attached {filename}"
                )
            else:
                embed.add_field(name=name, value=f"- Content:\n```{content}```")

        await channel.send(embed=embed, files=files)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MessageEvents(bot))
