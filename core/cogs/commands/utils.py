from disnake.ext import commands

class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Utilities, self).__init__()

        self.bot = bot

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utilities(bot))
