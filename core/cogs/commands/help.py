from disnake.ext import commands


class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(HelpCommand, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(HelpCommand(bot))
