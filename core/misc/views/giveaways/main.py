import disnake
from disnake.ext import commands
from core.database.models.giveaways import VoiceEnum
from core.misc.embed import custom_embed
from core.misc.giveaway import Giveaway
from core.misc.views.giveaways import *


class CreateModal(disnake.ui.Modal):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            title="Create new giveaway",
            custom_id="create_giveaway",
            components=[
                disnake.ui.TextInput(
                    label="Prize",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="Enter a prize",
                    max_length=100,
                    custom_id="prize",
                ),
                disnake.ui.TextInput(
                    label="Description",
                    style=disnake.TextInputStyle.paragraph,
                    required=False,
                    min_length=1,
                    max_length=200,
                    placeholder="Enter a description",
                    custom_id="description",
                ),
                disnake.ui.TextInput(
                    label="Winners",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="1",
                    custom_id="winners",
                ),
                disnake.ui.TextInput(
                    label="Duration",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="1d 1h 1m 1s (1 day, 1 hour, 1 minute, 1 second)",
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
                "❌ The number of winners must be a number", ephemeral=True
            )
            return
        if int(winners) < 1:
            await interaction.send(
                "❌ The number of winners must be greater than 0", ephemeral=True
            )
            return
        embed = custom_embed(
            title="Create giveaway",
            description=f"{description or ''}\n- Prize: **{prize}**\n- Winners: **{winners}**\n- Channel: {interaction.channel.mention}\nMaybe you want to change the channel?",
        )
        await interaction.send(embed=embed, ephemeral=True, view = GiveawaySettingsChannel(interaction, self.bot, prize, description, winners, duration, False))
    