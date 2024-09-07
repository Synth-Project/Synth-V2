from disnake.ext import commands


class Backup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Backup, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Backup(bot))
