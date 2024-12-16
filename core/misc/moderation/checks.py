import disnake
from disnake.ext.commands import (
    BadArgument,
    MemberConverter,
    UserConverter,
    CommandError,
)

from core.misc.embed import CustomEmbed

from functools import wraps
from typing import Union, Optional, Callable


class ModerationResolver:
    """
    Resolves and validates members for moderation commands.
    """

    def __init__(self, interaction: disnake.ApplicationCommandInteraction):
        self.interaction = interaction
        self.member_converter = MemberConverter()
        self.user_converter = UserConverter()

    async def resolve(
        self,
        member: Union[int, str, disnake.Member, disnake.User],
        *,
        for_unban: bool = False,
        for_unmute: bool = False,
        check_bot: bool = False,
    ) -> Optional[Union[disnake.Member, disnake.User]]:
        """
        Resolves a user or member and validates them for a specific moderation action.

        :param member: The user or member to resolve.
        :param for_unban: If True, allows resolving banned users.
        :param for_unmute: If True, validates that the user is muted.
        :param check_bot: If True, performs bot-specific validation.

        :return: The resolved member or user, or None if validation fails.
        """
        resolved = await self._resolve_member(member, for_unban)
        if not resolved:
            return None

        if not await self._validate_member(resolved, for_unban, for_unmute, check_bot):
            return None

        return resolved

    async def _resolve_member(
        self, member: Union[int, str, disnake.Member, disnake.User], for_unban: bool
    ) -> Optional[Union[disnake.Member, disnake.User]]:
        """
        Attempts to resolve a member or user by various methods.

        :param member: The member or user to resolve.
        :param for_unban: If True, allows resolving banned users.
        :return: The resolved member or user, or None if resolution fails.
        """
        if isinstance(member, (disnake.Member, disnake.User)):
            return self.interaction.guild.get_member(member.id) or member

        try:
            return await self.member_converter.convert(self.interaction, str(member))
        except (CommandError, BadArgument):
            if for_unban:
                return (
                    await self.user_converter.convert(self.interaction, str(member))
                    or None
                )

        return None

    async def _validate_member(
        self,
        member: Union[disnake.Member, disnake.User],
        for_unban: bool,
        for_unmute: bool,
        check_bot: bool,
    ) -> bool:
        """
        Validates the resolved member for specific moderation actions.

        :param member: The member to validate.
        :param for_unban: If True, allows resolving banned users.
        :param for_unmute: If True, validates that the user is muted.
        :param check_bot: If True, performs bot-specific validation.

        :return: True if the member is valid, False otherwise.
        """
        author = self.interaction.author

        if member.id == author.id:
            return await self._send_error("You can't perform this action on yourself")

        if check_bot and member.bot:
            return await self._send_error("You can't perform this action on a bot")

        if for_unban:
            return await self._validate_unban(member)

        if (
            for_unmute
            and getattr(member, "_communication_disabled_until", None) is None
        ):
            return await self._send_error(
                f"{member.mention} is not muted in this guild."
            )

        if isinstance(member, disnake.Member):
            return await self._validate_hierarchy(member, author)

        return True

    async def _validate_unban(self, member: disnake.User) -> bool:
        """
        Validates if the user is banned in the guild.

        :param member: The user to validate.

        :return: True if the user is banned in the guild, False otherwise.
        """
        banned_users = {ban.user.id for ban in await self.interaction.guild.bans()}
        if member.id not in banned_users:
            return await self._send_error(
                f"{member.mention} (`{member.id}`) is not banned in this guild."
            )

        return True

    async def _validate_hierarchy(
        self, member: disnake.Member, author: disnake.Member
    ) -> bool:
        """
        Validates role hierarchy between the author and the target member.

        :param member: The member to validate.
        :param author: The author of the interaction.

        :return: True if the hierarchy is valid, False otherwise.
        """
        if member.top_role >= author.top_role:
            return await self._send_error(
                f"Your role is not higher than {member.mention}'s role."
            )

        if (
            member.top_role >= self.interaction.guild.me.top_role
            and author.id != self.interaction.guild.owner_id
        ):
            return await self._send_error(
                f"{member.mention}'s role is higher than mine."
            )
        return True

    async def _send_error(self, message: str) -> bool:
        """
        Sends an error message to the interaction.

        :param message: The error message to send.

        :return: False
        """
        error_embed = CustomEmbed.error_embed(
            description=message, author=self.interaction.author
        )
        await self.interaction.response.send_message(
            embed=error_embed.get_embed(), ephemeral=True
        )
        return False


def resolve_member(
    *, for_unban: bool = False, for_unmute: bool = False, check_bot: bool = False
) -> Callable:
    """
    A decorator to resolve and validate members for moderation commands.

    :param for_unban: If True, allows resolving banned users.
    :param for_unmute: If True, validates that the user is muted.
    :param check_bot: If True, performs bot-specific validation.

    :return: The decorated function.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            member: Union[int, str, disnake.Member, disnake.User],
            *args,
            **kwargs,
        ):
            resolver = ModerationResolver(interaction)
            resolved_member = await resolver.resolve(
                member, for_unban=for_unban, for_unmute=for_unmute, check_bot=check_bot
            )

            if not resolved_member:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "Sorry, I couldn't find that member.", ephemeral=True
                    )
                return None

            return await func(self, interaction, resolved_member, *args, **kwargs)

        return wrapper

    return decorator
