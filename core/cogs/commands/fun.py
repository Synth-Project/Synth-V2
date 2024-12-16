from disnake.ext import commands


class FunCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(FunCommands, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(FunCommands(bot))
