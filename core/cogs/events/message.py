from disnake.ext import commands


class MessageLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(MessageLogging, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MessageLogging(bot))
