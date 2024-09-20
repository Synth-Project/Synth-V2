from disnake.ext import commands


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Giveaway, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Giveaway(bot))
