import disnake

from typing import Union, Tuple, Optional

from core.misc.embed import CustomEmbed


async def resolve_member(
    interaction: disnake.ApplicationCommandInteraction,
    member: Union[int, str, disnake.Member, disnake.User],
    for_unban: bool,
) -> Optional[disnake.Member]:
    """
    Resolves a user or member to a guild member.

    Args:
        interaction: The interaction context.
        member: The target member or user to resolve.
        for_unban: If True, skips checks for member existence in the guild.

    Returns:
        The resolved disnake.Member object or None if the member is not found.
    """
    if isinstance(member, disnake.User):
        return interaction.guild.get_member(member.id)
    return member if for_unban or isinstance(member, disnake.Member) else None


def check_self_action(
    interaction: disnake.ApplicationCommandInteraction, member: disnake.Member
) -> Optional[disnake.Embed]:
    """
    Checks if the action is being performed on the interaction author.

    Args:
        interaction: The interaction context.
        member: The target member to check.

    Returns:
        An error embed if the check fails, otherwise None.
    """
    if member == interaction.author:
        error_embed = CustomEmbed.error_embed(
            author=interaction.author,
            description="You can't perform this action on yourself.",
        )
        return error_embed.get_embed()

    return None


def check_bot_action(
    interaction: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    check_bot: bool,
) -> Optional[disnake.Embed]:
    """
    Checks if the action is being performed on a bot.

    Args:
        interaction: The interaction context.
        member: The target member to check.
        check_bot: Whether to include bots in the check.

    Returns:
        An error embed if the check fails, otherwise None.
    """
    if check_bot and member.bot:
        error_embed = CustomEmbed.error_embed(
            author=interaction.author,
            description="You can't perform this action on a bot.",
        )
        return error_embed.get_embed()
    return None


def check_role_hierarchy(
    interaction: disnake.ApplicationCommandInteraction, member: disnake.Member
) -> Optional[disnake.Embed]:
    """
    Checks if the user's role is higher than the target member's role.

    Args:
        interaction: The interaction context.
        member: The target member to check.

    Returns:
        An error embed if the user's role is not higher, otherwise None.
    """
    if member.top_role >= interaction.author.top_role:
        error_embed = CustomEmbed.error_embed(
            author=interaction.author,
            description=f"Your role is not higher than {member.mention}'s role.",
        ).get_embed()

        return error_embed
    return None


def check_bot_role_hierarchy(
    interaction: disnake.ApplicationCommandInteraction, member: disnake.Member
) -> Optional[disnake.Embed]:
    """
    Checks if the bot's role is higher than the target member's role.

    Args:
        interaction: The interaction context.
        member: The target member to check.

    Returns:
        An error embed if the bot's role is not higher, otherwise None.
    """
    bot_member = interaction.guild.me
    if member.top_role >= bot_member.top_role and not interaction.author.guild.owner:
        error_embed = CustomEmbed.error_embed(
            author=interaction.author,
            description=f"{member.mention}'s role is higher than mine. I can't perform this action.",
        ).get_embed()

        return error_embed
    return None


def check_mute_time(
    interaction: disnake.ApplicationCommandInteraction, str_time: int
) -> Optional[disnake.Embed]:
    """
    Checks if the mute time is within valid bounds.

    Args:
        interaction: The interaction context.
        str_time: The mute duration in seconds.

    Returns:
        An error embed if the mute time is invalid, otherwise None.
    """
    if not 60 <= str_time <= 2419200:
        error_embed = CustomEmbed.error_embed(
            author=interaction.author,
            description="Mute time must be between 1 minute and 28 days.",
        ).get_embed()
        return error_embed
    return None


async def common_checks(
    interaction: disnake.ApplicationCommandInteraction,
    member: Union[int, str, disnake.Member, disnake.User],
    check_bot: bool = False,
    for_unban: bool = False,
    for_mute: bool = False,
    str_time: Optional[int] = None,
) -> Tuple[bool, Optional[disnake.Embed]]:
    """
    Perform common validation checks for moderation actions.

    Args:
        interaction: The interaction context.
        member: The target member or user to validate.
        check_bot: Whether to include bots in validation.
        for_unban: If True, skips member existence checks.
        for_mute: If True, validates mute-specific conditions.
        str_time: The mute duration in seconds, if applicable.

    Returns:
        A tuple where the first element is True if all checks pass,
        and the second element is an error embed if a check fails.
    """
    resolved_member = await resolve_member(interaction, member, for_unban)

    if not resolved_member and not for_unban:
        error_embed = CustomEmbed.error_embed(
            author=interaction.author, description="Member not found in the guild."
        ).get_embed()
        return False, error_embed

    checks = [
        check_self_action(interaction, resolved_member),
        check_bot_action(interaction, resolved_member, check_bot),
        check_role_hierarchy(interaction, resolved_member) if not for_unban else None,
        check_bot_role_hierarchy(interaction, resolved_member) if check_bot else None,
        check_mute_time(interaction, str_time) if for_mute else None,
    ]

    for error in checks:
        if error:
            return False, error

    return True, None
