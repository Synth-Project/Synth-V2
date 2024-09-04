from disnake.ext import commands
import disnake
from core.misc.embed import custom_embed
from core.misc.views.dev.main import DevMainView

class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Dev, self).__init__()
        self.bot = bot

    @commands.slash_command(name = "dev", dm_permission=True)
    async def dev(self, interaction):
        embed = custom_embed(
            title = "👔 | Dev Panel",
            description = "Welcome to the Dev Panel. Use the buttons below to navigate.",
        )

        await interaction.send(embed=embed, ephemeral=True, view = DevMainView(self.bot))


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Dev(bot))