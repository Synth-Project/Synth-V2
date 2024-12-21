import datetime

import disnake
from disnake.ext import commands
from disnake.utils import utcnow

from core.misc.moderation.misc import str_to_seconds, hms
from core.misc.embed import CustomEmbed


class ModerationActions:
    def __init__(self, bot: commands.Bot, interaction: disnake.Interaction) -> None:
        self.bot = bot
        self.interaction = interaction

    async def mute(
        self,
        member: disnake.Member,
        mute_time: int,
        reason: str = "Not specified",
        crossmute: bool = False,
    ) -> None:
        """
        Mutes a user for a specified time.

        :param member: The member to mute.
        :param mute_time: The time to mute the member.
        :param reason: The reason for the mute.
        :param crossmute: If True, the user will be muted in all channels.
        :return: None
        """
        str_time = await str_to_seconds(mute_time)

        if str_time == 0:
            error_embed = CustomEmbed().error_embed(
                description=f"<:disallow:1171111636573093929> | Invalid mute time format."
            )
            return await self.interaction.send(embed=error_embed.get_embed())

        unmute_time = utcnow() + datetime.timedelta(seconds=str_time)

        embed = CustomEmbed(
            title="<:mute:1170712518725992529> Successfully muted ",
            description=(
                f"**Member:** {member.mention} ({member})\n"
                f"**Administrator:** {self.interaction.user.mention} ({self.interaction.user})\n"
                f"**Time:** {str(await hms(float(str_time)))}\n"
                f"**Reason:** {reason}\n"
                f"**Unmute date:** <t:{int(unmute_time.timestamp())}>"
            ),
        ).get_embed()

        await member.edit(
            timeout=disnake.utils.utcnow() + datetime.timedelta(seconds=str_time)
        )
        await self.interaction.send(embed=embed) and not crossmute

        try:
            embed.title = f"<:mute:1170712518725992529> You were muted {"(crossmute)" if crossmute else ""}"
            embed.description = (
                f"**Administrator:** {self.interaction.user.mention} ({self.interaction.user})\n"
                f"**Server:** {self.interaction.guild.name}\n"
                f"**Time:** {str(await hms(float(str_time)))}\n"
                f"**Reason:** {reason}\n"
                f"**Unmute date:** <t:{int(unmute_time.timestamp())}>"
            )
            await member.send(embed=embed)
        except (disnake.HTTPException, disnake.Forbidden):
            pass

    async def kick(
        self, member: disnake.Member, reason: str, crosskick: bool = False
    ) -> None:
        """
        Kicks a user from this guild.

        :param member: The member to kick.
        :param reason: The reason for the kick.
        :param crosskick: If True, the user will be kicked from all servers.
        :return: None
        """
        embed = CustomEmbed(
            title="<:kick:1170712514288435271> Successfully kicked",
            description=(
                f"**Administrator:** {self.interaction.user.mention} ({self.interaction.user})\n"
                f"**Member:** {member.mention} ({member})\n"
                f"**Reason:** {reason}"
            ),
        ).get_embed()

        await self.interaction.send(embed=embed)

        try:
            embed.title = f"<:kick:1170712514288435271> You were kicked {"(crosskick)" if crosskick else ""}"
            embed.description = (
                f"**Administrator:** {self.interaction.user.mention} ({self.interaction.user})\n"
                f"**Reason:** {reason}\n"
                f"**Server:** {self.interaction.guild.name}"
            )
            await member.send(embed=embed)
        except (disnake.HTTPException, disnake.Forbidden):
            pass

        await member.kick(reason=reason)

    async def ban(
        self,
        member: disnake.User,
        reason: str,
        ban_time: str = None,
        crossban: bool = False,
    ) -> None:
        """
        Bans a user from this guild.

        :param member: The member to ban.
        :param reason: The reason for the ban.
        :param ban_time: The time to ban the member.
        :param crossban: If True, the user will be banned from all servers.
        :return: None
        """
        embed = CustomEmbed(
            title="<:ban:1170712517308317756> Successfully banned",
            description=(
                f"**Administrator:** {self.interaction.user.mention} ({self.interaction.user})\n"
                f"**Member:** {member.mention} ({member})\n"
                f"**Reason:** {reason}"
            ),
        ).get_embed()

        await self.interaction.send(embed=embed)

        try:
            embed.title = f"<:ban:1170712517308317756> You were banned {"(crossban)" if crossban else ""}"
            embed.description = (
                f"**Administrator:** {self.interaction.user.mention} ({self.interaction.user})\n"
                f"**Reason:** {reason}\n"
                f"**Server:** {self.interaction.guild.name}"
            )
            await member.send(embed=embed)
        except (disnake.HTTPException, disnake.Forbidden):
            pass

        await self.interaction.guild.ban(
            member, reason=f"{self.interaction.user}: {reason}"
        )
