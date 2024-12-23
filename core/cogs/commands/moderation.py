import datetime

import disnake
from disnake.ext import commands
from disnake.utils import utcnow

from core.database.repositories.user import UserRepository
from core.misc.moderation.misc import str_to_seconds
from core.misc.moderation.actions import ModerationActions
from core.misc.moderation.checks import resolve_member
from core.misc.moderation.misc import (
    generate_mute_list,
    generate_ban_list,
    generate_warns_list,
)
from core.misc.color import BasicColors
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

    @moderation.sub_command_group(name="warn")
    async def warn(self, _: disnake.ApplicationCommandInteraction) -> None:
        pass

    @warn.sub_command(name="add", description="Add a warn to a specific user")
    @resolve_member()
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def add_warn(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        *,
        reason: str = "Not specified",
        remove_at: str | None = None,
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

        str_time = await str_to_seconds(remove_at) if remove_at else 0

        if str_time == 0 and remove_at:
            error_embed = CustomEmbed().error_embed(
                description=f"<:disallow:1171111636573093929> | Invalid remove warn time format."
            )
            return await interaction.send(embed=error_embed.get_embed())

        remove_warn_at = utcnow() + datetime.timedelta(seconds=str_time)

        warn = await self.user_repository.add_warn(
            user_id=member.id,
            warned_by=interaction.user.id,
            reason=reason,
            remove_at=remove_warn_at,
        )

        embed = CustomEmbed(
            description=(
                f"- **Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"- **Member:** {member.mention} ({member})\n"
                f"- **Reason:** {reason or 'No reason provided'}\n"
                f"- **Total warns:** {warn.warn_id}\n"
                f"- **Remove at**: {disnake.utils.format_dt(remove_warn_at, style='f') if remove_at else "Never"}"
            ),
            thumbnail=member.display_avatar.url,
        ).get_embed()
        embed.set_author(
            name=f"Successfully warned", icon_url=interaction.user.display_avatar.url
        )

        await interaction.send(embed=embed)

        try:
            dm_embed = CustomEmbed(
                description=(
                    f"- **Administrator:** {interaction.user.mention} ({interaction.user})\n"
                    f"- **Reason:** {reason or 'No reason provided'}\n"
                    f"- **Server:** {interaction.guild.name}\n"
                    f"- **Total warns:** {warn.warn_id}\n"
                    f"- **Remove at**: {disnake.utils.format_dt(remove_warn_at, style='f') if remove_at else "Never"}"
                ),
                thumbnail=member.display_avatar.url,
            ).get_embed()
            dm_embed.set_author(
                name="You were warned", icon_url=interaction.user.display_avatar.url
            )

            await member.send(embed=dm_embed)
        except (disnake.HTTPException, disnake.Forbidden):
            pass

    @warn.sub_command(name="remove", description="Remove a specific warn from a user")
    @resolve_member()
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def remove_warn(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        warn_id: str,
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

        if not warn_id.isdigit():
            selected_warn = warn_id.split(":")[0]

        warn_id = int(selected_warn)

        try:
            warn = await self.user_repository.get_warn(
                user_id=member.id, warn_id=warn_id
            )
            warn_removed = await self.user_repository.remove_warn(
                user_id=member.id, warn_id=warn_id
            )

            if warn_removed:
                embed = CustomEmbed(
                    description=(
                        f"- **Administrator:** {interaction.user.mention} ({interaction.user})\n"
                        f"- **Member:** {member.mention} ({member})\n"
                        f"- **Warned by:** {(await interaction.guild.get_or_fetch_member(warn.warned_by)).mention}\n"
                        f"- **Warn reason:** {warn.reason}\n"
                        f"- **Warn date:** {disnake.utils.format_dt(warn.date, "f") if warn.date else "Unknown"}\n"
                    ),
                    thumbnail=member.display_avatar.url,
                ).get_embed()

                embed.set_author(
                    name=f"Successfully removed warn #{warn.warn_id}",
                    icon_url=interaction.user.display_avatar.url,
                )
                await interaction.send(embed=embed)
            else:
                error_embed = CustomEmbed.error_embed(
                    title="<:error:1170712514288435271> Warn Not Found",
                    description="No warn with this ID was found for the user.",
                )
                await interaction.send(embed=error_embed.get_embed())

        except Exception as e:
            print(e)

    @warn.sub_command(name="view", description="View warns of a user")
    @commands.has_permissions(kick_members=True, ban_members=True)
    async def view_warns(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member = None,
    ) -> None:
        """
        View all warns for a user

        Args:
            interaction: The interaction context.
            member: The member to view warns for.

        Returns:
            None
        """

        member = member or interaction.user

        warns = await self.user_repository.get_warns(user_id=member.id)

        if not warns:
            embed = CustomEmbed(
                title="<:info:1169685342077583480> User Warns",
                description=f"{member.mention} currently has no warns.",
            ).get_embed()

            return await interaction.send(embed=embed)

        warn_pages = [
            CustomEmbed(
                title=f"<:info:1169685342077583480> Warn #{warn.warn_id}",
                description=(
                    f"- **Member:** {member.mention} ({member})\n"
                    f"- **Administrator:** {moderator.mention} ({moderator})\n"
                    f"- **Reason:** {warn.reason or 'No reason provided'}\n"
                    f"- **Date:** {disnake.utils.format_dt(warn.date.timestamp(), style='f')}\n"
                    f"- **Removes at:** {disnake.utils.format_dt(warn.remove_at.timestamp(), style='f') if warn.remove_at else 'Never'}"
                ),
                thumbnail=member.display_avatar.url,
            ).get_embed()
            for warn in warns
            for moderator in [
                await interaction.guild.get_or_fetch_member(warn.warned_by)
            ]
        ]

        await interaction.send(
            embed=warn_pages[0],
            view=(
                CreatePaginator(warn_pages)
                if len(warn_pages) > 1
                else disnake.utils.MISSING
            ),
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
        match list:
            case "mutes":
                embeds, error = await generate_mute_list(interaction)
            case "bans":
                embeds, error = await generate_ban_list(interaction)
            case "warns":
                all_warns = await self.user_repository.get_all_warns()
                embeds, error = await generate_warns_list(interaction, all_warns)

        if error:
            error_embed = disnake.Embed(title=error, color=BasicColors.ERROR)
            error_embed.set_footer(
                text=interaction.user, icon_url=interaction.user.avatar
            )
            return await interaction.send(embed=error_embed)

        paginator = (
            CreatePaginator(embeds=embeds, author_id=interaction.author.id, timeout=600)
            if len(embeds) > 1
            else disnake.utils.MISSING
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
        )
        await interaction.send(embed=embed.get_embed())

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
        await ModerationActions(self.bot, interaction).kick(
            member=member, reason=reason
        )

    @moderation.sub_command(name="mute", description="Mute a user for a specified time")
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
        await ModerationActions(self.bot, interaction).mute(
            member=member, mute_time=mute_time, reason=reason
        )

    @moderation.sub_command(name="unmute", description="Unmute a user")
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
        )

        await member.edit(timeout=None)
        await interaction.send(embed=embed.get_embed())

        try:
            embed.title = "<:unmute:1169690521472614500> You were unmuted"
            embed.description = (
                f"**Administrator:** {interaction.user.mention} ({interaction.user})\n"
                f"**Server:** {interaction.guild.name}\n"
            )
            await member.send(embed=embed.get_embed())
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
        await ModerationActions(self.bot, interaction).cross_ban(
            member=member, reason=reason
        )

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
        await ModerationActions(self.bot, interaction).cross_kick(
            member=member, reason=reason
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))
