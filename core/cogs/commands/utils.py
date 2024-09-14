import disnake
from disnake.ext import commands

from core.misc.misc import mention_slash


class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Utilities, self).__init__()
        self.bot = bot

    @commands.slash_command()
    async def hello(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.send(content=mention_slash(interaction.guild, "player play"))


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utilities(bot))
