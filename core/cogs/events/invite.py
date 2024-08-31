from disnake.ext import commands
import disnake
from core.bot import ITracker


class InviteLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(InviteLogging, self).__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        original_invite: disnake.Invite = await ITracker().get_invite_db(member)
        if original_invite:
            print(original_invite.code)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(InviteLogging(bot))
