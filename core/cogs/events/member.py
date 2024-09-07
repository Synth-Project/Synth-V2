from disnake.ext import commands


class MemberLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(MemberLogging, self).__init__()

        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MemberLogging(bot))
