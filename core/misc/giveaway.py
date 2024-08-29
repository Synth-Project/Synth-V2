import asyncio
from datetime import timedelta
import datetime
import random
import re
import disnake
from disnake.ext import commands, tasks
from core.misc.embed import custom_embed, CreatePaginator
from core.database.models.giveaways import GiveawayModel
from typing import Optional

time_units = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}


async def get_member_ids(message_id) -> Optional[GiveawayModel]:
    # print(message.channel.id)
    result = await GiveawayModel.get_or_none(message_id=message_id)
    if not result:
        return None

    return result


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

        if interaction.author.id in data:
            await interaction.send(
                "✅ You have successfully left the giveaway", ephemeral=True
            )
            data.members.remove(interaction.author.id)
        else:
            await interaction.send(
                "✅ You have successfully entered the giveaway", ephemeral=True
            )
            data.members.append(interaction.author.id)
        update = await GiveawayModel.filter(message_id=message_id).first()
        update.members = data.members
        await update.save()

    @disnake.ui.button(
        label="Entries", style=disnake.ButtonStyle.gray, custom_id="giveaway_members"
    )
    async def members(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        message_id = interaction.message.id
        nigg = []
        yaeblan = 0
        data = await get_member_ids(message_id)
        if data is None:
            await interaction.send("❌ Giveaway not found", ephemeral=True)
            return

        for member in data.members:
            member = await self.bot.get_or_fetch_user(member)
            nigg.append(f"**{member.name}** / **{member.id}**")
            yaeblan += 1

        embeds = CreatePaginator.generate_embeds(
            items=nigg,
            items_per_embed=25,
            empty_list_message="This giveaway has no entries.",
            title="Entries of the giveaway",
            description=f"All entries: **{yaeblan}**",
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
    ) -> None:
        duration_regex = r"(\d+)([dhms])"

        matches = re.findall(duration_regex, duration)

        duration_delta = timedelta()
        for value, unit in matches:
            if unit in time_units:
                time_unit = time_units[unit]
                try:
                    duration_delta += timedelta(**{time_unit: int(value)})
                except OverflowError:
                    await interaction.send(
                        "❌ The maximum giveaway duration has been exceeded"
                    )
                    return

        end_time = datetime.datetime.now() + duration_delta
        embed = custom_embed(
            f"🎉 | Giveaway",
            f"{description or ''}\n- Prize: **{prize}**\n- Winners: **{winners}**\n- Ends: {disnake.utils.format_dt(end_time, style = 'R')}",
        )
        await interaction.send(".", ephemeral=True)
        L = await check_chat(interaction.channel)
        if not L:
            await interaction.edit_original_message(
                "❌ The channel is unavailable to me. Give me more permissions"
            )
            return
        await interaction.delete_original_response()
        msg = await interaction.channel.send(embed=embed)
        await GiveawayModel.create(
            prize=prize,
            winners=winners,
            end_time=end_time.timestamp(),
            channel_id=interaction.channel.id,
            message_id=msg.id,
            ended=False,
            members=[],
        )
        await msg.edit(
            view=GiveawayView(
                self.bot,
            ),
        )


async def check_chat(channel: disnake.abc.GuildChannel) -> bool:
    try:
        msg = await channel.send(".")
        await msg.delete()
        return True
    except:
        return False
