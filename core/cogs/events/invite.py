import disnake
from disnake.ext import commands

from core.bot import ITracker
from core.logger.logger import logger


class InviteLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(InviteLogging, self).__init__()
        self.bot = bot

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member) -> None:
        await ITracker().add_member(member)

    @commands.Cog.listener("on_member_remove")
    async def on_member_remove(self, member: disnake.Member) -> None:
        logger.info(f"Member {member} left the guild {member.guild.name}")
        await ITracker().delete_member(member)

    @commands.slash_command(name="invite")
    async def invite(self, interaction) -> None:
        pass

    @invite.sub_command(name="list")
    async def invite_list(self, interaction) -> None:
        invited_members = await ITracker().get_invited_members(
            user_id=interaction.user.id, guild=interaction.guild
        )
        if invited_members:
            member_names = ["- " + str(member.name) for member in invited_members]
            await interaction.response.send_message(
                "You invited the following members:\n" + "\n".join(member_names)
            )
        else:
            await interaction.response.send_message("You haven't invited anyone yet.")

    @invite.sub_command(name="inviter")
    async def invite_inviter(self, interaction) -> None:
        inviter = await ITracker().get_inviter(
            member_id=interaction.user.id, guild=interaction.guild
        )
        if inviter:
            await interaction.response.send_message(
                f"You were invited by {inviter.name}."
            )
        else:
            await interaction.response.send_message("I couldn't find who invited you.")

    @invite.sub_command(name="leaderboard")
    async def invite_leaderboard(self, interaction) -> None:
        await interaction.response.send_message("Not implemented yet.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(InviteLogging(bot))
