from disnake.ext import commands


class ErrorLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(ErrorLogging, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ErrorLogging(bot))
