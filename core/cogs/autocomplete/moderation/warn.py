import disnake
from disnake.ext import commands

from core.cogs.commands.moderation import Moderation
from core.misc.moderation.misc import (
    TIME_UNITS,
    CYRILLIC_MAP,
    SIMPLIFIED_TIME_UNITS,
    str_to_seconds,
    hms,
)
from core.database.repositories.user import UserRepository


class WarnAutocomplete(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_repository = UserRepository()

    @Moderation.add_warn.autocomplete("remove_at")
    async def remove_at_autocomplete(
        self, interaction: disnake.Interaction, current: str
    ) -> list[str]:
        suggestions = []

        if not current:
            return ["❌ | No time provided"]

        current = current.lower().replace(".", "")

        # if not current.isdigit():
        #     return ["❌ | Invalid time format"]

        # try:
        #     current_num = int(current)
        # except ValueError:
        #     return ["❌ | Invalid time format"]
        for c in current:
            if c in TIME_UNITS.keys():
                if await str_to_seconds(current) != 0:
                    return [current]
        else:
            # if current:
            try:
                current_num = int(current)
            except ValueError:
                return ["❌ | Invalid time format"]

        suggestions = [
            f"{current} {unit}{'s' if current_num > 1 else ''}"
            for unit in SIMPLIFIED_TIME_UNITS
        ]
        # suggestions = await hms(current_num, True)

        return suggestions[:25]

    @Moderation.remove_warn.autocomplete("warn_id")
    async def remove_warn_autocomplete(
        self, interaction: disnake.ApplicationCommandInteraction, current: str
    ) -> list[str]:
        member = interaction.filled_options.get("member")

        autocomplete_result = []

        warns = await self.user_repository.get_warns(user_id=member)

        autocomplete_result.extend(
            [
                f"{warn.warn_id}: {warn.reason[:50] + '...'} | {warn.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                for warn in sorted(warns, key=lambda x: x.warn_id, reverse=True)
            ]
        )

        return autocomplete_result[:25]

        # if not current or not current.replace(".", "", 1).isdigit():
        #     return suggestions

        # suggestions = [f"{current}"]


def setup(bot: commands.Bot):
    bot.add_cog(WarnAutocomplete(bot))
