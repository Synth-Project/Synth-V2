from datetime import datetime
from typing import Union
import disnake
from disnake.ext import commands
from core.database.models.reminder import ReminderType
from core.database.repositories.reminder import ReminderRepository
from core.misc.embed import custom_embed
from core.misc.emoji import StandartEmoji


class MainReminderView(disnake.ui.View):
    def __init__(
        self, bot: Union[commands.Bot, commands.InteractionBot], time: str, text: str
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.time = time
        self.text = text

    @disnake.ui.string_select(
        options=[
            disnake.SelectOption(
                label="DM me",
                value="dm",
                description="Send a reminder to your DM",
                emoji=StandartEmoji.MEMBERS.value,
            ),
            disnake.SelectOption(
                label="Right here",
                value="channel",
                description="Send a reminder to this channel",
                emoji=StandartEmoji.TEXT_CHANNEL.value,
            ),
            disnake.SelectOption(
                label="Exit",
                value="exit",
                description="Just exit",
                emoji=StandartEmoji.DENY.value,
            ),
        ]
    )
    async def select_callback(
        self, select: disnake.ui.StringSelect, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        if select.values[0] == "exit":
            await interaction.delete_original_message()
        else:
            await ReminderRepository().save_remind(
                author_id=interaction.author.id,
                text=self.text,
                time=datetime.now().timestamp() + int(self.time),
                channel_id=(
                    interaction.channel.id
                    if select.values[0] == "channel"
                    else interaction.author.id
                ),
                type=(
                    ReminderType.DM
                    if select.values[0] == "dm"
                    else ReminderType.CHANNEL
                ),
            )
            embed = custom_embed("Reminder", "Reminder was created!")
            embed.add_field(name="Text", value=self.text, inline=True)
            embed.add_field(
                name="Time",
                value=disnake.utils.format_dt(
                    datetime.fromtimestamp(datetime.now().timestamp() + int(self.time)),
                    "R",
                ),
                inline=True,
            )
            await interaction.edit_original_response(embed=embed, view=None)
