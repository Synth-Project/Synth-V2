import disnake
from disnake.ext.commands import MemberConverter, UserConverter, CommandError
from functools import wraps
from typing import Union, Optional, Callable

from core.misc.embed import CustomEmbed


class ModerationResolver:
    def __init__(self, interaction: disnake.ApplicationCommandInteraction):
        self.interaction = interaction
        self.member_converter = MemberConverter()
        self.user_converter = UserConverter()

    async def resolve(
        self,
        member: Union[int, str, disnake.Member, disnake.User],
        *,
        for_unban: bool = False,
        check_bot: bool = False,
    ) -> Optional[Union[disnake.Member, disnake.User]]:
        resolved_member = await self._resolve_member(member, for_unban)
        if not resolved_member:
            return None

        try:
            await self._validate_member(resolved_member, for_unban, check_bot)
        except CommandError as e:
            error_embed = CustomEmbed.error_embed(
                description=str(e), author=self.interaction.author
            )
            await self.interaction.response.send_message(
                embed=error_embed.get_embed(), ephemeral=True
            )
            return None

        return resolved_member

    async def _resolve_member(
        self, member: Union[int, str, disnake.Member, disnake.User], for_unban: bool
    ) -> Optional[Union[disnake.Member, disnake.User]]:
        if isinstance(member, disnake.Member):
            return member
        if isinstance(member, disnake.User):
            return self.interaction.guild.get_member(member.id) or member

        try:
            return await self.member_converter.convert(self.interaction, str(member))
        except CommandError:
            if for_unban:
                try:
                    return await self.user_converter.convert(
                        self.interaction, str(member)
                    )
                except CommandError:
                    pass
        return None

    async def _validate_member(
        self,
        member: Union[disnake.Member, disnake.User],
        for_unban: bool = False,
        check_bot: bool = False,
    ) -> None:
        if member.id == self.interaction.author.id:
            raise CommandError("You can't perform this action on yourself")

        if check_bot and getattr(member, "bot", False):
            raise CommandError("You can't perform this action on a bot")

        if not for_unban and isinstance(member, disnake.Member or disnake.User):
            if member.top_role >= self.interaction.author.top_role:
                raise CommandError(
                    f"Your role is not higher than {member.mention}'s role"
                )

            if (
                member.top_role >= self.interaction.guild.me.top_role
                and self.interaction.author.id != self.interaction.guild.owner_id
            ):
                raise CommandError(f"{member.mention}'s role is higher than mine")


def resolve_member(*, for_unban: bool = False, check_bot: bool = False):
    """
    A decorator to resolve and validate members for moderation commands.

    Args:
        for_unban: Skip guild member checks if True
        check_bot: Include bot-specific checks if True
    """

    def decorator(func: Callable):
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
                member, for_unban=for_unban, check_bot=check_bot
            )

            if not resolved_member:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "Member not found.", ephemeral=True
                    )
                return None

            return await func(self, interaction, resolved_member, *args, **kwargs)

        return wrapper

    return decorator
