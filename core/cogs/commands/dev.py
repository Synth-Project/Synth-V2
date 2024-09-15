from disnake.ext import commands
from core.misc.embed import CustomEmbed
from core.misc.views.dev.bot_manager import DevBotManagerView
from core.misc.views.dev.console import DevConsoleView
from core.misc.views.dev.main import DevMainView


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Dev, self).__init__()
        self.bot = bot

    @staticmethod
    def embed():
        embed = CustomEmbed(
            title="👔 | Dev Panel",
            description="Welcome to the Dev Panel. Use the buttons below to navigate.",
        ).get_embed()
        return embed

    async def cog_load(self):
        self.bot.add_view(DevMainView(self.bot))
        self.bot.add_view(DevBotManagerView(self.bot))
        self.bot.add_view(DevConsoleView(self.bot))

    @commands.slash_command(name="dev", dm_permission=True)
    async def dev(self, interaction):
        await interaction.send(
            embed=self.embed(), ephemeral=True, view=DevMainView(self.bot)
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Dev(bot))
