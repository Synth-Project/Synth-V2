from disnake.ext import commands
from core.bot import Bot
from core.misc.embed import CustomEmbed
from core.misc.views.dev.bot_manager import DevBotManagerView
from core.misc.views.dev.console import DevConsoleView
from core.misc.views.dev.main import DevMainView
from gettext import gettext as _
import os


class Dev(commands.Cog):
    def __init__(self, bot: "Bot"):
        super(Dev, self).__init__()
        self.bot = bot

    @staticmethod
    def embed():
        embed = CustomEmbed(
            title="👔 | Dev Panel",
            description="Welcome to the Dev Panel. Use the buttons below to navigate.",
        ).get_embed()
        return embed

    async def cog_load(self):
        self.bot.add_view(DevMainView(self.bot))
        self.bot.add_view(DevBotManagerView(self.bot))
        self.bot.add_view(DevConsoleView(self.bot))

    @commands.slash_command(name="dev", dm_permission=True)
    async def dev(self, interaction):
        await interaction.send(
            embed=self.embed(), ephemeral=True, view=DevMainView(self.bot)
        )

    @commands.slash_command(name="translate", dm_permission=True)
    async def translate(self, interaction):
        user_locale = interaction.locale.value
        # user_locale = "ru"

        title = await self.bot.translation.get(user_locale, _("Hello"))
        description = await self.bot.translation.get(user_locale, _("World"))

        # loc.set_language(user_locale)
        # title = loc.gettext("Hello")
        # description = loc.gettext("World")
        embed = CustomEmbed(title=title, description=description).get_embed()
        await interaction.response.send_message(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Dev(bot))
