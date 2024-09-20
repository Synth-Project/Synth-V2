from disnake.ext import commands


class InviteLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(InviteLogging, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(InviteLogging(bot))
