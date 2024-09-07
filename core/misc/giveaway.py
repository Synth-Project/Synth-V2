import asyncio
from datetime import timedelta
import datetime
import re
import aiohttp
import disnake
from disnake.ext import commands
from core.misc.embed import custom_embed, CreatePaginator
from core.database.models.giveaway import GiveawayModel, VoiceEnum
from typing import Optional, Union

time_units = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}


async def get_member_ids(message_id) -> Optional[GiveawayModel]:
    # print(message.channel.id)
    result = await GiveawayModel.get_or_none(message_id=message_id)

    if not result:
        return None
    return result


async def _get_channel(bot, channel_id: int) -> Union[disnake.abc.GuildChannel, bool]:
    """Fetch a channel and return whether it was successful."""
    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        return channel
    except disnake.HTTPException:
        return False


class GiveawayView(disnake.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @disnake.ui.button(
        label="Join",
        style=disnake.ButtonStyle.blurple,
        custom_id="giveaway_accept",
    )
    async def accept(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        message_id = interaction.message.id
        data = await get_member_ids(message_id)

        if interaction.author.id in data.members:
            await interaction.send(
                "✅ You have successfully left the giveaway", ephemeral=True
            )
            data.members.remove(interaction.author.id)
        else:
            await interaction.send(
                "✅ You have successfully entered the giveaway", ephemeral=True
            )
            data.members.append(interaction.author.id)

        # update = await GiveawayModel.filter(message_id=message_id).first()
        # update.members = data.members
        # await update.save()
        await GiveawayModel.filter(message_id=message_id).update(members=data.members)

    @disnake.ui.button(
        label="Entries", style=disnake.ButtonStyle.gray, custom_id="giveaway_members"
    )
    async def members(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        message_id = interaction.message.id
        data = await get_member_ids(message_id)

        members_list = [
            f"**{member.name}** / **{member.id}**"
            for member in await asyncio.gather(
                *(self.bot.get_or_fetch_user(member) for member in data.members)
            )
        ]
        total_entries = len(members_list)

        embeds = CreatePaginator.generate_embeds(
            items=members_list,
            items_per_embed=25,
            empty_list_message="This giveaway has no entries.",
            title="Entries of the giveaway",
            description=f"All entries: **{total_entries}**",
        )

        await interaction.send(
            embed=embeds[0],
            view=CreatePaginator(embeds, interaction.author.id, 120),
            ephemeral=True,
        )

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        # return await super().interaction_check(interaction)
        data = await get_member_ids(interaction.message.id)
        if data is None:
            await interaction.send("❌ Giveaway not found", ephemeral=True)
            return False

        if not data.ended:
            voice = interaction.author.voice

            match data.voice:
                case VoiceEnum.SPECIFIED_VC:
                    if not voice or data.voice_id != voice.channel.id:
                        voice = await _get_channel(self.bot, data.voice_id)
                        if voice:
                            await interaction.send(
                                f"❌ You need to join to the required voice channel: {voice.mention}",
                                ephemeral=True,
                            )
                            return False

                case VoiceEnum.SPECIFIED_SG:
                    if not voice or data.voice_id != voice.channel.id:
                        stage = await _get_channel(self.bot, data.voice_id)
                        if stage:
                            await interaction.send(
                                f"❌ You need to join to the required stage channel: {stage.mention}",
                                ephemeral=True,
                            )
                            return False

                case VoiceEnum.SPECIFIED_CG:
                    if not voice or data.voice_id != voice.channel.category_id:
                        category = await _get_channel(self.bot, data.voice_id)
                        if category:
                            await interaction.send(
                                f"❌ You need to join to the required category: {category.mention}",
                                ephemeral=True,
                            )
                            return False

                case VoiceEnum.ANY_VC:
                    if not voice or voice.channel.type != disnake.ChannelType.voice:
                        await interaction.send(
                            "❌ You need to join to the any voice channel",
                            ephemeral=True,
                        )
                        return False

                case VoiceEnum.ANY_SG:
                    if (
                        not voice
                        or voice.channel.type != disnake.ChannelType.stage_voice
                    ):
                        await interaction.send(
                            "❌ You need to join to the any stage channel",
                            ephemeral=True,
                        )
                        return False

        return True


class Giveaway:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def create(
        self,
        interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        voice: VoiceEnum,
        required_channel: Optional[disnake.abc.GuildChannel] = None,
        channel_to_send: disnake.abc.GuildChannel = None,
        image_uri: Optional[str] = None,
    ) -> None:
        if not await self.check_channel(channel_to_send):
            await interaction.edit_original_message(
                f"❌ | The channel {channel_to_send.mention} is unavailable to me. Give me more permissions",
                embed=None,
                view=None,
            )
            return

        if not await self.check_duration(duration) or not await self.check_image(
            image_uri
        ):
            return

        await interaction.delete_original_response()
        duration_delta = timedelta()
        for value, unit in re.findall(r"(\d+)([dhms])", duration):
            if unit in time_units:
                duration_delta += timedelta(**{time_units[unit]: int(value)})

        end_time = datetime.datetime.now() + duration_delta
        ends = disnake.utils.format_dt(end_time, style="R")
        desc = (
            f"{description or ''}\n"
            f"- Prize: **{prize}**\n"
            f"- Winners: **{winners}**\n"
            f"- Ends: {ends}\n"
        )
        embed = custom_embed(
            "🎉 | Giveaway",
            desc,
        ).set_image(url=image_uri if image_uri else None)

        msg = await channel_to_send.send(embed=embed)
        await GiveawayModel.create(
            prize=prize,
            winners=winners,
            end_time=end_time.timestamp(),
            channel_id=channel_to_send.id,
            message_id=msg.id,
            ended=False,
            members=[],
            voice=voice,
            voice_id=required_channel.id if required_channel else 0,
        )

        await msg.edit(view=GiveawayView(self.bot))

    async def check_duration(self, duration: str) -> bool:
        """
        Validate the duration string.

        Args:
            duration (str): The duration string.

        Returns:
            bool: Whether the duration is valid or not.
        """
        if not duration:
            return False

        try:
            duration_delta = timedelta()
            for value, unit in re.findall(r"(\d+)([dhms])", duration):
                if unit not in time_units:
                    return False
                try:
                    duration_delta += timedelta(**{time_units[unit]: int(value)})
                except (ValueError, OverflowError):
                    return False
            return True
        except Exception:
            return False

    async def check_channel(self, channel: disnake.abc.GuildChannel) -> bool:
        """Check if the bot has permission to send messages in the given channel.

        Args:
            channel (disnake.abc.GuildChannel): The channel to check.

        Returns:
            bool: Whether the bot has permission to send messages in the channel or not.
        """
        try:
            msg = await channel.send(".")
            await msg.delete()
            return True
        except:
            return False

    async def check_image(self, image_uri: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(image_uri) as response:
                    # Проверяем тип содержимого
                    content_type = response.headers.get("Content-Type", "")
                    if content_type.startswith("image"):
                        return True
            return False
        except Exception:
            return False
