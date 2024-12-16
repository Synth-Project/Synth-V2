import os
import sys
import disnake
from disnake.ext import commands

from core.misc.views.base import CustomButton


class DevBotManagerView(disnake.ui.View):
    def __init__(self, bot: commands.Bot):
        super(DevBotManagerView, self).__init__(timeout=None)
        self.bot = bot
        from core.cogs.commands.dev import Dev, DevMainView

        self.add_item(
            CustomButton(row=0, view=DevMainView(self.bot), embed=Dev.embed())
        )

    @disnake.ui.button(
        label="Stop",
        emoji="⏹️",
        style=disnake.ButtonStyle.red,
        custom_id="dev_bot_manager_stop",
    )
    async def stop(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_message("Stopping...", ephemeral=True)
        await self.bot.close()

    @disnake.ui.button(
        label="Restart",
        emoji="🔄",
        style=disnake.ButtonStyle.green,
        custom_id="dev_bot_manager_restart",
    )
    async def restart(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_message(
            "Restarting...", ephemeral=True, delete_after=5
        )
        os.execl(sys.executable, sys.executable, "-m", "core.main.main")
