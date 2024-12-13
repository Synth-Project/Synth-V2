from datetime import datetime

import disnake
from disnake.ext import commands

from core.misc.moderation.checks import common_checks
from core.misc.moderation.misc import str_to_seconds, hms
from core.misc.embed import CustomEmbed


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Moderation, self).__init__()

        self.bot = bot

    @commands.slash_command(name="ban", description="Ban a user from this guild")
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        *,
        reason: str = None,
    ) -> None:
        """
        Ban a user from this guild

        Args:
            interaction: The interaction context.
            user: The user to ban.
            reason: The reason for the ban.

        Returns:
            None
        """
        embed = CustomEmbed().get_embed()

        check_result, error_embed = await common_checks(interaction, user.id)
        if not check_result:
            return await interaction.send(embed=error_embed)

        embed.title = "<:ban:1170712517308317756> Successfully banned"
        embed.description = (
            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
            f"**Member:** {user.mention} ({user})\n"
            f"**Reason:** {reason}"
        )
        await interaction.send(embed=embed)

        try:
            embed.title = "<:ban:1170712517308317756> You were banned"
            embed.description = (
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Reason:** {reason}\n"
                f"**Server:** {interaction.guild.name}"
            )
            await user.send(embed=embed)

        except (Exception, BaseException, disnake.Forbidden):
            pass

        await interaction.guild.ban(user, reason=f"{interaction.user}: {reason}")

    @commands.slash_command(name="unban", description="Unban a user on this guild")
    @commands.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
    ) -> None:
        """
        Unban a user on this guild

        Args:
            interaction: The interaction context.
            member: The member to unban.

        Returns:
            None
        """
        check_result, error_embed = await common_checks(
            interaction, member.id, for_unban=True
        )
        if not check_result:
            return await interaction.send(embed=error_embed)

        embed = CustomEmbed().get_embed()
        embed.title = "<:invite:1169690514430382160> Successfully unbanned"
        embed.description = (
            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
            f"**Member:** {member.mention} (`{id}`)"
        )

        await interaction.guild.unban(member)
        await interaction.send(embed=embed)

    @commands.slash_command(name="kick", description="Kick a user from this guild")
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def kick(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        *,
        reason: str = None,
    ) -> None:
        """
        Kick a user from this guild

        Args:
            interaction: The interaction context.
            member: The member to kick.
            reason: The reason for the kick.

        Returns:
            None
        """
        embed = CustomEmbed().get_embed()

        check_result, error_embed = await common_checks(interaction, member.id)
        if not check_result:
            return await interaction.send(embed=error_embed)

        embed.title = "<:kick:1170712514288435271> Successfully kicked"
        embed.description = (
            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
            f"**Member:** {member.mention} ({member})\n"
            f"**Reason:** {reason}"
        )
        await interaction.send(embed=embed)

        try:
            embed.title = "<:kick:1170712514288435271> You were kicked"
            embed.description = (
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Reason:** {reason}\n"
                f"**Server:** {interaction.guild.name}"
            )
            await member.send(embed=embed)

        except (Exception, BaseException, disnake.Forbidden):
            pass

        await member.kick(reason=reason)

    @commands.slash_command(name="mute", description="Mute a user for a specified time")
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def mute(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        mute_time: str,
        *,
        reason: str = "Not specified",
    ) -> None:
        """
        Mute a user

        Args:
            interaction: The interaction context.
            member: The member to mute.
            mute_time: The time to mute the member.
            reason: The reason for the mute.

        Returns:
            None
        """
        embed = CustomEmbed().get_embed()

        try:
            str_time = await str_to_seconds(mute_time)
        except ValueError:
            error_embed = CustomEmbed.error_embed(
                description=f"<:disallow:1171111636573093929> | Invalid mute time format."
            )
            return await interaction.send(embed=error_embed)

        check_result, error_embed = await common_checks(
            interaction, member, for_mute=True, str_time=str_time
        )
        if not check_result:
            return await interaction.send(embed=error_embed)

        embed.title = "<:mute:1170712518725992529> Successfully muted"
        embed.description = (
            f"**Member:** {member.mention} ({member})\n"
            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
            f"**Time:** {str(await hms(float(str_time)))}\n"
            f"**Reason:** {reason}\n"
            f"**Unmute date:** <t:{int(disnake.utils.utcnow()) + str_time}>"
        )
        await member.edit(
            timeout=disnake.utils.utcnow() + datetime.timedelta(seconds=str_time)
        )
        await interaction.send(embed=embed)

        try:
            embed.title = "<:mute:1170712518725992529> You were muted"
            embed.description = (
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Server:** {interaction.guild.name}\n"
                f"**Time:** {str(await hms(float(str_time)))}\n"
                f"**Reason:** {reason}\n"
                f"**Unmute date:** <t:{int(disnake.utils.utcnow() + float(str_time))}>"
            )
            await member.send(embed=embed)
        except (Exception, BaseException, disnake.Forbidden):
            pass


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))
