import datetime

import disnake
from disnake.ext import commands

from core.database.repositories.user import UserRepository
from core.misc.moderation.actions import ModerationActions
from core.misc.moderation.checks import resolve_member
from core.misc.moderation.misc import (
    generate_mute_list,
    generate_ban_list,
    generate_warns_list,
)
from core.misc.embed import CustomEmbed
from core.misc.paginator import CreatePaginator


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Moderation, self).__init__()

        self.bot = bot
        self.user_repository = UserRepository()

    @commands.slash_command(name="moderation")
    async def moderation(self, _: disnake.ApplicationCommandInteraction):
        pass

    @moderation.sub_command(name="warn", description="Warn a user")
    @resolve_member()
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def warn(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        *,
        reason: str = None,
    ) -> None:
        """
        Warn a user

        Args:
            interaction: The interaction context.
            member: The member to warn.
            reason: The reason for the warn.

        Returns:
            None
        """
        warn = await self.user_repository.add_warn(
            user_id=member.id, warned_by=interaction.user.id, reason=reason
        )

        embed = CustomEmbed(
            title="<:warn:1170712514288435271> Successfully warned",
            description=(
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Member:** {member.mention} ({member})\n"
                f"**Reason:** {reason or 'No reason provided'}\n"
                f"**Warn ID:** {warn.warn_id}"
            ),
        ).get_embed()

        await interaction.send(embed=embed)

        try:
            dm_embed = CustomEmbed(
                title="<:warn:1170712514288435271> You were warned",
                description=(
                    f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                    f"**Reason:** {reason or 'No reason provided'}\n"
                    f"**Server:** {interaction.guild.name}\n"
                    f"**Warn ID:** {warn.warn_id}"
                ),
            ).get_embed()
            await member.send(embed=dm_embed)
        except (disnake.HTTPException, disnake.Forbidden):
            pass

    @moderation.sub_command(
        name="remove_warn", description="Remove a specific warn from a user"
    )
    @resolve_member()
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def remove_warn(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        warn_id: int,
    ) -> None:
        """
        Remove a specific warn from a user

        Args:
            interaction: The interaction context.
            member: The member to remove warn from.
            warn_id: The ID of the warn to remove.

        Returns:
            None
        """
        try:
            # Attempt to remove the specific warn
            warn_removed = await self.user_repository.remove_warn(
                user_id=member.id, warn_id=warn_id
            )

            if warn_removed:
                embed = CustomEmbed(
                    title="<:success:1170712514288435271> Warn Removed",
                    description=(
                        f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                        f"**Member:** {member.mention} ({member})\n"
                        f"**Warn ID:** {warn_id}"
                    ),
                    color=BasicColors.SUCCESS,
                ).get_embed()
                await interaction.send(embed=embed)
            else:
                embed = CustomEmbed(
                    title="<:error:1170712514288435271> Warn Not Found",
                    description=(
                        f"**Member:** {member.mention} ({member})\n"
                        f"**Warn ID:** {warn_id}\n"
                        "No warn with this ID was found for the user."
                    ),
                    color=BasicColors.ERROR,
                ).get_embed()
                await interaction.send(embed=embed)

        except Exception as e:
            await interaction.send(
                CustomEmbed(title="Error", description=str(e), color=BasicColors.ERROR)
            )

    @moderation.sub_command(name="view_warns", description="View warns for a user")
    # @resolve_member()
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def view_warns(
        self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member
    ) -> None:
        """
        View all warns for a user

        Args:
            interaction: The interaction context.
            member: The member to view warns for.

        Returns:
            None
        """
        try:
            warns = await self.user_repository.get_warns(user_id=member.id)

            if not warns:
                embed = CustomEmbed(
                    title="<:info:1170712514288435271> User Warns",
                    description=f"{member.mention} has no warns.",
                    color=BasicColors.DEFAULT,
                ).get_embed()
                await interaction.send(embed=embed)
                return

            warn_pages = []
            for warn in warns:
                moderator = await interaction.guild.get_or_fetch_member(warn.warned_by)
                warn_page = CustomEmbed(
                    title=f"Warn #{warn.warn_id}",
                    description=(
                        f"**Member:** {member.mention} ({member})\n"
                        f"**Moderator:** {moderator.mention} ({moderator})\n"
                        f"**Reason:** {warn.reason or 'No reason provided'}\n"
                        f"**Date:** {disnake.utils.format_dt(warn.date.timestamp(), style='f')}"
                    ),
                    color=BasicColors.WARNING,
                ).get_embed()
                warn_pages.append(warn_page)

            await interaction.send(
                embed=warn_pages[0],
                view=(
                    CreatePaginator(warn_pages)
                    if len(warn_pages) > 1
                    else disnake.utils.MISSING
                ),
            )

        except Exception as e:
            await interaction.send(
                embed=CustomEmbed(
                    title="Error", description=str(e), color=BasicColors.ERROR
                ).get_embed()
            )

    @moderation.sub_command(name="show", description="Show moderation lists")
    async def show_list(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        list: str = commands.Param(
            choices=["bans", "mutes", "warns"],
            description="Choose which list to show",
        ),
    ):
        # processors = {
        #     "mutes": self._process_mute_list,
        #     "bans": self._process_ban_list,
        # }

        # embeds, error = await processors[list_type](interaction)
        match list:
            case "mutes":
                embeds, error = await generate_mute_list(interaction)
            case "bans":
                embeds, error = await generate_ban_list(interaction)
            case "warns":
                all_warns = await self.user_repository.get_all_warns()
                embeds, error = await generate_warns_list(interaction, all_warns)

        if error:
            error_embed = disnake.Embed(
                color=BasicColors.ERROR, description=description
            )
            error_embed.set_footer(
                text=interaction.user, icon_url=interaction.user.avatar
            )
            return await interaction.send(embed=error_embed)

        paginator = CreatePaginator(
            embeds=embeds, author_id=interaction.author.id, timeout=600
        )
        await interaction.send(embed=embeds[0], view=paginator)

    @moderation.sub_command(name="ban", description="Ban a user from this guild")
    @resolve_member()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.User,
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
        # embed = CustomEmbed(
        #     title="<:ban:1170712517308317756> Successfully banned",
        #     description=(
        #         f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
        #         f"**Member:** {member.mention} ({member})\n"
        #         f"**Reason:** {reason}"
        #     ),
        # ).get_embed()

        # await interaction.send(embed=embed)

        # try:
        #     embed.title = "<:ban:1170712517308317756> You were banned"
        #     embed.description = (
        #         f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
        #         f"**Reason:** {reason}\n"
        #         f"**Server:** {interaction.guild.name}"
        #     )
        #     await member.send(embed=embed)
        # except (disnake.HTTPException, disnake.Forbidden):
        #     pass

        # await interaction.guild.ban(member, reason=f"{interaction.user}: {reason}")

        await ModerationActions(self.bot, interaction).ban(member, reason)

    @commands.slash_command(name="unban", description="Unban a user on this guild")
    @resolve_member(for_unban=True)
    @commands.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.User,
    ) -> None:
        """
        Unban a user on this guild.

        Args:
            interaction: The interaction context.
            member: The member to unban.

        Returns:
            None
        """
        await interaction.guild.unban(member)

        embed = CustomEmbed(
            title="<:invite:1169690514430382160> Successfully unbanned",
            description=(
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Member:** {member.mention} (`{member.id}`)\n"
            ),
        ).get_embed()
        await interaction.send(embed=embed)

    @moderation.sub_command(name="kick", description="Kick a user from this guild")
    @resolve_member()
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
        # embed = CustomEmbed(
        #     title="<:kick:1170712514288435271> Successfully kicked",
        #     description=(
        #         f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
        #         f"**Member:** {member.mention} ({member})\n"
        #         f"**Reason:** {reason}"
        #     ),
        # ).get_embed()

        # await interaction.send(embed=embed)

        # try:
        #     embed.title = "<:kick:1170712514288435271> You were kicked"
        #     embed.description = (
        #         f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
        #         f"**Reason:** {reason}\n"
        #         f"**Server:** {interaction.guild.name}"
        #     )
        #     await member.send(embed=embed)
        # except (disnake.HTTPException, disnake.Forbidden):
        #     pass

        # await member.kick(reason=reason)

        await ModerationActions(self.bot, interaction).kick(
            member=member, reason=reason
        )

    @commands.slash_command(name="mute", description="Mute a user for a specified time")
    @resolve_member()
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
        # str_time = await str_to_seconds(mute_time)

        # if str_time == 0:
        #     error_embed = CustomEmbed().error_embed(
        #         description=f"<:disallow:1171111636573093929> | Invalid mute time format."
        #     )
        #     return await interaction.send(embed=error_embed.get_embed())

        # unmute_time = utcnow() + datetime.timedelta(seconds=str_time)

        # embed = CustomEmbed(
        #     title="<:mute:1170712518725992529> Successfully muted",
        #     description=(
        #         f"**Member:** {member.mention} ({member})\n"
        #         f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
        #         f"**Time:** {str(await hms(float(str_time)))}\n"
        #         f"**Reason:** {reason}\n"
        #         f"**Unmute date:** <t:{int(unmute_time.timestamp())}>"
        #     ),
        # ).get_embed()

        # await member.edit(
        #     timeout=disnake.utils.utcnow() + datetime.timedelta(seconds=str_time)
        # )
        # await interaction.send(embed=embed)

        # try:
        #     embed.title = "<:mute:1170712518725992529> You were muted"
        #     embed.description = (
        #         f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
        #         f"**Server:** {interaction.guild.name}\n"
        #         f"**Time:** {str(await hms(float(str_time)))}\n"
        #         f"**Reason:** {reason}\n"
        #         f"**Unmute date:** <t:{int(unmute_time.timestamp())}>"
        #     )
        #     await member.send(embed=embed)
        # except (disnake.HTTPException, disnake.Forbidden):
        #     pass

        await ModerationActions(self.bot, interaction).mute(
            member=member, mute_time=mute_time, reason=reason
        )

    @commands.slash_command(name="unmute", description="Unmute a user")
    @resolve_member(for_unmute=True)
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def unmute(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
    ) -> None:
        """
        Unmute a user

        Args:
            interaction: The interaction context.
            member: The member to unmute.

        Returns:
            None
        """
        embed = CustomEmbed(
            title="<:unmute:1169690521472614500> Successfully unmuted",
            description=(
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Member:** {member.mention} ({member})"
            ),
        ).get_embed()

        await member.edit(timeout=None)
        await interaction.send(embed=embed)

        try:
            embed.title = "<:unmute:1169690521472614500> You were unmuted"
            embed.description = (
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Server:** {interaction.guild.name}\n"
            )
            await member.send(embed=embed)
        except (disnake.HTTPException, disnake.Forbidden):
            pass

    @moderation.sub_command(
        name="crossban",
        description="Ban user from all servers, where the requester is administrator",
    )
    @resolve_member()
    @commands.has_permissions(administrator=True)
    async def cross_ban(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.User,
        reason: str = None,
    ):
        embed = CustomEmbed().get_embed()
        success_servers: int = 0

        for guild in self.bot.guilds:
            requested_from_permissions = (
                await guild.fetch_member(interaction.user.id)
            ).guild_permissions

            if not requested_from_permissions.administrator:
                continue

            if member := await guild.fetch_member(member.id):
                try:
                    await guild.ban(member, reason=reason)

                    if not guild == interaction.guild:
                        embed.title = "<:kick:1170712514288435271> Crossban"
                        embed.description = (
                            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                            f"**Member:** {member} (`{member.id}`)\n"
                            f"**Reason:** {reason}"
                        )
                        await guild.text_channels[0].send(embed=embed)

                    success_servers += 1
                except (disnake.HTTPException, disnake.Forbidden):
                    continue

        embed.title = "<:kick:1170712514288435271> Crossban Success"
        embed.description = (
            f"**Kicked from {success_servers} servers.**\n"
            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
            f"**Member:** {member} (`{member.id}`)\n"
            f"**Reason:** {reason}"
        )
        await interaction.send(embed=embed)

    @moderation.sub_command(
        name="crosskick",
        description="Kick user from all servers, where the requester is administrator",
    )
    @resolve_member()
    @commands.has_permissions(administrator=True)
    async def cross_kick(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.User,
        reason: str = None,
    ):
        embed = CustomEmbed().get_embed()
        success_servers: int = 0

        for guild in self.bot.guilds:
            requested_from_permissions = (
                await guild.fetch_member(interaction.user.id)
            ).guild_permissions

            if not requested_from_permissions.administrator:
                continue

            if member := await guild.fetch_member(member.id):
                try:
                    await guild.kick(member, reason=reason)

                    if not guild == interaction.guild:
                        embed.title = "<:kick:1170712514288435271> Crosskick"
                        embed.description = (
                            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                            f"**Member:** {member} (`{member.id}`)\n"
                            f"**Reason:** {reason}"
                        )
                        await guild.text_channels[0].send(embed=embed)

                    success_servers += 1
                except (disnake.HTTPException, disnake.Forbidden):
                    continue

        embed.title = "<:kick:1170712514288435271> Crosskick Success"
        embed.description = (
            f"**Kicked from {success_servers} servers.**\n"
            f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
            f"**Member:** {member} (`{member.id}`)\n"
            f"**Reason:** {reason}"
        )
        await interaction.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))
