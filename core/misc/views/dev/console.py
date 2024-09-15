import disnake
from disnake.ext import commands
from core.misc.embed import CustomEmbed
from core import info_logger, debug_logger, error_logger
from core.misc.views.base import CustomButton


class DevConsoleView(disnake.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        from core.cogs.commands.dev import Dev, DevMainView
        self.add_item(CustomButton(row=1, view=DevMainView(self.bot), embed=Dev.embed()))

    @disnake.ui.select(
        cls=disnake.ui.Select,
        placeholder="Select log type",
        options=[
            disnake.SelectOption(label="Info", emoji="🔎", value="info"),
            disnake.SelectOption(label="Debug", emoji="🔎", value="debug"),
            disnake.SelectOption(label="Error", emoji="🔎", value="error"),
        ],
        custom_id="dev_console_select_log",
    )
    async def select_log(
        self, select: disnake.ui.Select, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        log_name = select.values[0]
        log_content = {
            "info": info_logger.getvalue(),
            "debug": debug_logger.getvalue(),
            "error": error_logger.getvalue(),
        }[log_name]

        embed = CustomEmbed(
            title=f"🔧 | Console {log_name.capitalize()} Logs"
        ).get_embed()
        embed.description = (
            f"```{log_content}```" if log_content else f"No logs available."
        )
        await interaction.edit_original_message(embed=embed)
