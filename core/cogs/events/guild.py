from disnake.ext import commands


class GuildLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(GuildLogging, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(GuildLogging(bot))
