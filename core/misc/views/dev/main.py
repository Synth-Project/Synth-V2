import disnake
from disnake.ext import commands
from core.misc.embed import custom_embed


class DevMainView(disnake.ui.View):
    def __init__(self, bot: commands.Bot):
        super(DevMainView, self).__init__()

        self.bot = bot

    @disnake.ui.select(
        options=[
            disnake.SelectOption(label="❌", value="close"),
            disnake.SelectOption(label="Bot Manager", emoji="🤖", value="bot_manager"),
            disnake.SelectOption(label="Cog Manager", emoji="🔨", value="cog_manager"),
            disnake.SelectOption(
                label="Command Manager", emoji="✨", value="command_manager"
            ),
            disnake.SelectOption(
                label="Event Manager", emoji="📝", value="event_manager"
            ),
            disnake.SelectOption(label="Console", emoji="🔧", value="console"),
        ]
    )
    async def callback(
        self, select: disnake.ui.Select, interaction: disnake.MessageInteraction
    ):
        selected_option = select.values[0]
        match selected_option:
            case "close":
                await interaction.delete_original_response()
            case _:
                await self.bot.get_command("dev").callback(interaction)
