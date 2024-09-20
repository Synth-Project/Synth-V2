from disnake.ext import commands


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Settings, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Settings(bot))
