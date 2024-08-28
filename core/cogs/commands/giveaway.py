from disnake.ext import commands, tasks
import disnake
from core.misc.giveaway import GiveawayView
from core.database.models.giveaways import GiveawayModel
from core.misc.views.giveaway import CreateModal
import random
import datetime


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Giveaway, self).__init__()
        self.bot = bot

    async def cog_load(self):
        self.check_gw.start()
        self.bot.add_view(GiveawayView(self.bot))

    async def end_gw(self, giveaway_data):
        try:
            channel: disnake.TextChannel = self.bot.get_channel(
                giveaway_data["channel_id"]
            ) or await self.bot.fetch_channel(giveaway_data["channel_id"])
            msg = await channel.fetch_message(giveaway_data.get("message_id"))
        except Exception:
            if await GiveawayModel.get(giveaway_data.get("message_id")) is None:
                return
            await GiveawayModel.delete(giveaway_data.get("message_id"))
            return
        view = disnake.ui.View.from_message(msg)

        winner_amount = giveaway_data["winners"]
        embed = msg.embeds[0]
        embed.title = f"🎉 | Розыгрыш окончен"

        users = [await self.bot.fetch_user(W) for W in giveaway_data["members"]]
        if len(users) < winner_amount:
            winners = random.sample(users, len(users))
        else:
            winners = random.sample(users, winner_amount)

        winners = ", ".join(w.mention for w in winners)
        view.children[0].disabled = True
        view.children[1].disabled = True
        await msg.edit(embed=embed, content=winners, view=view)
        if len(users) > 0:
            await msg.reply(
                f"⭐ Розыгрыш окончен, {'победители' if winner_amount > 1 else 'победитель'}: "
                + winners
            )
        else:
            await msg.reply(f"❗Недостаточно участников чтобы окончить розыгрыш.")
        giveaway_data["ended"] = True
        await GiveawayModel.update_or_create(giveaway_data)

    @tasks.loop(seconds=1)
    async def check_gw(self):
        giveaways = list(await GiveawayModel.all())
        for giveaway in giveaways:
            giveaway_data = await GiveawayModel.get_or_none(giveaway)
            if giveaway_data is not None:
                if giveaway_data["ended"]:
                    if (
                        datetime.datetime.now().timestamp()
                        > giveaway_data["end_time"] + 260000
                    ):
                        await GiveawayModel.delete(giveaway_data)
                if giveaway_data["ended"] == False:
                    if datetime.datetime.now().timestamp() > giveaway_data["end_time"]:
                        await self.end_gw(giveaway_data)

    @commands.slash_command()
    async def giveaway(self, _) -> None:
        pass

    @giveaway.sub_command(
        description="Create a giveaway",
        name="create",
    )
    async def create(self, interaction):
        await interaction.response.send_modal(CreateModal(self.bot))

    @giveaway.sub_command(description="Reroll a giveaway", name="reroll")
    async def reroll(self, interaction, message_id, winners: int):
        await interaction.response.defer(ephemeral=True)
        if not message_id.isdigit():
            await interaction.send("Айди должно быть числом.", ephemeral=True)
            return
        try:
            giveaway_msg = await interaction.channel.fetch_message(message_id)
        except disnake.NotFound:
            await interaction.send("Сообщение не найдено.", ephemeral=True)
            return

        if giveaway_msg.author == self.bot:
            if (
                not giveaway_msg.embeds
                or not giveaway_msg.embeds[0].title == f"🎉 | Розыгрыш"
                or not giveaway_msg.embeds[0].title == f"🎉 | Розыгрыш окончен"
            ):
                await interaction.send(
                    "Сообщение не является розыгрышом.", ephemeral=True
                )
                return

        if winners <= 0:
            await interaction.send(
                "Количество победителей должно быть больше нуля.", ephemeral=True
            )
            return

        datb = await GiveawayModel.get_or_none(message_id)
        if datb is None:
            await interaction.send("Розыгрыш не найден.", ephemeral=True)
            return

        users = [await self.bot.fetch_user(W) for W in datb.get("members", [])]
        winners_mention = random.sample(users, min(winners, len(users)))

        winners_mention = ", ".join(w.mention for w in winners_mention)

        await interaction.send(
            content="Всё!",
            ephemeral=True,
        )
        await interaction.channel.send(
            f"⭐ {'Новые победители: ' if winners > 1 else 'Новый победитель: '}{winners_mention}"
        )
        await giveaway_msg.edit(
            content=f"⭐ {'Новые победители: ' if winners > 1 else 'Новый победитель: '}{winners_mention}"
        )

    @giveaway.sub_command(
        description="End a giveaway",
        name="end",
    )
    async def end(self, interaction, message_id):
        await interaction.response.defer(ephemeral=True)
        if not message_id.isdigit():
            await interaction.send("Айди должно быть числом.", ephemeral=True)
            return
        try:
            giveaway_msg = await interaction.channel.fetch_message(message_id)
        except disnake.NotFound:
            await interaction.send("Сообщение не найдено.", ephemeral=True)
            return

        if giveaway_msg.author == self.bot:
            if (
                not giveaway_msg.embeds
                or not giveaway_msg.embeds[0].title == "Розыгрыш"
                or not giveaway_msg.embeds[0].title == "Розыгрыш окончен"
            ):
                await interaction.send(
                    "Сообщение не является розыгрышом.", ephemeral=True
                )
                return

        if giveaway_msg.embeds[0].title == f"🎉 | Розыгрыш окончен":
            await interaction.send("Розыгрыш уже окончен.", ephemeral=True)
            return

        datb = await GiveawayModel.get_or_none(message_id)
        if datb is None:
            await interaction.send("Розыгрыш не найден.", ephemeral=True)
            return

        await self.end_gw(datb)
        await interaction.send("Розыгрыш окончен", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Giveaway(bot))
