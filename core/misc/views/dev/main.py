import disnake
from disnake.ext import commands
from core.misc.embed import CustomEmbed
from core.misc.views.dev.bot_manager import DevBotManagerView
from core.misc.views.dev.console import DevConsoleView


class DevMainView(disnake.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(DevSelect(self.bot))


class DevSelect(disnake.ui.Select):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            placeholder="Select a management option",
            options=[
                disnake.SelectOption(
                    label="Bot Manager", emoji="🤖", value="bot_manager"
                ),
                disnake.SelectOption(
                    label="Cog Manager", emoji="🔨", value="cog_manager"
                ),
                disnake.SelectOption(label="Console", emoji="🔧", value="console"),
            ],
            custom_id="dev_select",
        )
        self.bot = bot

    async def callback(self, interaction: disnake.Interaction) -> None:
        selected_option = self.values[0]
        match selected_option:
            case "bot_manager":
                embed = CustomEmbed(
                    title="🤖 | Bot Manager",
                    description="Welcome to the Bot Manager. Use the buttons below to navigate.",
                ).get_embed()
                await interaction.response.edit_message(
                    embed=embed, view=DevBotManagerView(self.bot)
                )
            case "console":
                embed = CustomEmbed(
                    title="🔧 | Console",
                    description="Welcome to the Console. Use the buttons below to navigate.",
                ).get_embed()
                await interaction.response.edit_message(
                    embed=embed, view=DevConsoleView(self.bot)
                )
