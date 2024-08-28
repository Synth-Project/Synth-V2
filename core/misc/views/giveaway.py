import secrets
import disnake
from disnake.ext import commands
from core.misc.giveaway import Giveaway

class CreateModal(disnake.ui.Modal):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            title="Создание розыгрыша",
            custom_id="create_giveaway",
            components=[
                disnake.ui.TextInput(
                    label="Приз",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="Введите приз",
                    max_length=100,
                    custom_id="prize",
                ),
                disnake.ui.TextInput(
                    label="Описание",
                    style=disnake.TextInputStyle.paragraph,
                    required=False,
                    min_length=1,
                    max_length=200,
                    placeholder="Введите описание",
                    custom_id="description",
                ),
                disnake.ui.TextInput(
                    label="Кол-во победителей",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="Введите кол-во победителей",
                    custom_id="winners",
                ),
                disnake.ui.TextInput(
                    label="Длительность",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="1d 1h 1m 1s (1 день, 1 час, 1 минута, 1 секунда)",
                    custom_id="duration",
                ),
            ],
        )
        self.bot = bot

    async def callback(self, interaction):
        prize = interaction.text_values["prize"]
        description = (
            interaction.text_values["description"]
            if interaction.text_values["description"]
            else None
        )
        winners = interaction.text_values["winners"]
        duration = interaction.text_values["duration"].lower()
        if not winners.isdigit():
            await interaction.send(
                "Кол-во победителей должно быть числом", ephemeral=True
            )
            return
        if int(winners) < 1:
            await interaction.send(
                "Кол-во победителей должно быть больше 0", ephemeral=True
            )
            return
        await Giveaway(self.bot).create(
            interaction, prize, description, winners, duration
        )