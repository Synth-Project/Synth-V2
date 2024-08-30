import asyncio
from datetime import timedelta
import datetime
import re
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


async def _check_chat(channel: disnake.abc.GuildChannel) -> bool:
    try:
        msg = await channel.send(".")
        await msg.delete()
        return True
    except:
        return False


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
        if data is None:
            await interaction.send("❌ Giveaway not found", ephemeral=True)
            return

        match data.voice:
            case VoiceEnum.SPECIFIED_VC:
                if (
                    interaction.author.voice
                    or data.voice_id != interaction.author.voice.channel.id
                ):
                    voice = await _get_channel(self.bot, data.voice_id)
                    if voice:
                        await interaction.send(
                            f"❌ You need to join to the required voice channel: {voice.mention}",
                            ephemeral=True,
                        )
                        return

            case VoiceEnum.SPECIFIED_SG:
                if (
                    interaction.author.voice
                    or data.voice_id != interaction.author.voice.channel.id
                ):
                    stage = await _get_channel(self.bot, data.voice_id)
                    if stage:
                        await interaction.send(
                            f"❌ You need to join to the required stage channel: {voice.mention}",
                            ephemeral=True,
                        )
                        return

            case VoiceEnum.SPECIFIED_CG:
                if (
                    interaction.author.voice
                    or data.voice_id != interaction.author.voice.channel.category_id
                ):
                    category = await _get_channel(self.bot, data.voice_id)
                    if category:
                        await interaction.send(
                            f"❌ You need to join to the required category: {category.mention}",
                            ephemeral=True,
                        )
                        return

            case VoiceEnum.ANY_VC:
                if (
                    interaction.author.voice
                    or interaction.author.voice.channel.type
                    != disnake.ChannelType.voice
                ):
                    await interaction.send(
                        "❌ You need to join to the any voice channel",
                        ephemeral=True,
                    )
                    return

            case VoiceEnum.ANY_SG:
                if (
                    interaction.author.voice
                    or interaction.author.voice.channel.type
                    != disnake.ChannelType.stage_voice
                ):
                    await interaction.send(
                        "❌ You need to join to the any stage channel",
                        ephemeral=True,
                    )
                    return

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
        await GiveawayModel.filter(message_id=message_id).update(
            members=data.members
        )

    @disnake.ui.button(
        label="Entries", style=disnake.ButtonStyle.gray, custom_id="giveaway_members"
    )
    async def members(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        message_id = interaction.message.id

        if not (data := await get_member_ids(message_id)):
            await interaction.send("❌ Giveaway not found", ephemeral=True)
            return

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
    ) -> None:
        if not await _check_chat(channel_to_send):
            await interaction.send(
                "❌ The channel is unavailable to me. Give me more permissions",
                ephemeral=True,
            )
            return

        # Parse duration
        duration_delta = timedelta()
        for value, unit in re.findall(r"(\d+)([dhms])", duration):
            if unit in time_units:
                try:
                    duration_delta += timedelta(**{time_units[unit]: int(value)})
                except OverflowError:
                    await interaction.send(
                        "❌ The maximum giveaway duration has been exceeded",
                        ephemeral=True,
                    )
                    return

        end_time = datetime.datetime.now() + duration_delta
        ends = disnake.utils.format_dt(end_time, style="R")
        embed = custom_embed(
            "🎉 | Giveaway",
            f"{description or ''}\n- Prize: **{prize}**\n- Winners: **{winners}**\n- Ends: {ends}",
        )

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
        # await interaction.delete_original_response()
