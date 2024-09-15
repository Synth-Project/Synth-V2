import glob
import os
from typing import Dict, List
import disnake
from disnake.ext import commands
from core import cog_paths

from core.misc.embed import CustomEmbed
from core.misc.views.base import CustomButton

class CogView(disnake.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        from core.cogs.commands.dev import Dev, DevMainView
        self.add_item(CustomButton(row=1, view=DevMainView(self.bot), embed=Dev.embed()))
        self.add_item(CogDropdown(self.bot))

    @staticmethod
    def embed():
        embed = CustomEmbed(
            title="🔨 | Cog Manager",
            description="Welcome to the Cog Manager. Use the buttons below to navigate.",
        ).get_embed()
        return embed

class CogDropdown(disnake.ui.Select):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cogs = self._get_cogs()
        self.items_per_page = 23
        self.page = 1

        self.options = self._get_options() or [
            disnake.SelectOption(
                emoji="<:crossmark:1282338837456224394>",
                label="Cogs not loaded",
                value="none",
            )
        ]
        super().__init__(
            placeholder="Choose a cog",
            min_values=1,
            max_values=1,
            options=self.options,
            disabled=not bool(self.cogs),
        )

    def _get_cogs(self) -> List[Dict[str, bool]]:
        """
        Get all loaded cogs with their status
        :return: List of dictionaries with cog names and their statuses
        :rtype: List[Dict[str, bool]]
        """
        cogs = []
        all_loaded_cogs = self.bot.cogs

        for path in cog_paths:
            for file_path in glob.glob(os.path.join(path, "*.py")):
                file_name = os.path.basename(file_path)

                if file_name == "__init__.py":
                    continue

                cog_name = f"{path.replace("/", ".")}.{file_name[:-3]}"
                cog_status = False
                cog_class = None
                
                for loaded_cog_name, loaded_cog_instance in all_loaded_cogs.items():
                    if loaded_cog_name.startswith(file_name[:-3].capitalize()) or loaded_cog_name == file_name[:-3].capitalize():
                        cog_status = True
                        cog_class = loaded_cog_instance.__class__.__name__
                        break
                    else:
                        cog_status = False
                        cog_class = None

                cogs.append({
                    "name": cog_name,
                    "status": cog_status,
                    "class": cog_class
                })

        return cogs

    def _get_options(self):
        """
        Get the select menu options for the current page.
        :return: A list of disnake.SelectOption objects
        :rtype: List[disnake.SelectOption]
        """
        start_idx = (self.page - 1) * self.items_per_page
        end_idx = self.page * self.items_per_page
        options = []

        if self.page > 1:
            options.append(
                disnake.SelectOption(emoji="◀️", label="Previous", value="previous")
            )

        for cog in self.cogs[start_idx:end_idx]:
            cog_name = cog["name"]
            status = bool(cog["status"])
            emoji = "✅" if status else "❌"
            options.append(
                disnake.SelectOption(
                    emoji=emoji,
                    label=cog_name,
                    value=cog_name,
                )
            )

        if end_idx < len(self.cogs):
            options.append(disnake.SelectOption(emoji="▶️", label="Next", value="next"))

        return options


    async def callback(self, interaction: disnake.MessageInteraction):
        """
        Callback for the dropdown menu

        Parameters:
            interaction (disnake.MessageInteraction): Interaction from the dropdown menu

        Return: None
        """
        selected_value = self.values[0]

        if selected_value == "next":
            self.page += 1
        elif selected_value == "previous":
            self.page -= 1
        else:
            cog_name = selected_value
            matching_cog = next((cog for cog in self.cogs if cog["name"] == cog_name), None)
            if matching_cog:
                if matching_cog["status"]:
                    if matching_cog["class"] != None:
                        cog = self.bot.get_cog(matching_cog["class"])
                        if not cog:
                            matching_cog["status"] = False
                    embed = CustomEmbed(
                        title=f"🔨 | Cog Manager: {matching_cog['name']}",
                    ).get_embed()
                    await interaction.response.edit_message(view=CogManagerView(self.bot, matching_cog))
                    return


        self.cogs = self._get_cogs()
        self.options = self._get_options()
        await interaction.response.edit_message(view=self)


class CogManagerView(disnake.ui.View):
    def __init__(self, bot: commands.Bot, cog_info: Dict[str, bool]) -> None:
        """Initialize the CogManagerView.

        Args:
            bot (commands.Bot): The bot instance.
            cog_info (Dict[str, bool]): A dictionary containing information about the cog.
                The dictionary should contain the keys "name", "status", and "class".
        """
        super().__init__(timeout=None)
        self.add_item(CustomButton(row=0, view=CogView(bot), embed=CogView.embed()))
        self.bot = bot
        self.cog_name = cog_info["name"]
        self.cog_status = cog_info["status"]
        self.cog_class = cog_info["class"]

        self.load_unload_cog.label = "Unload" if self.cog_status else "Load"
        self.load_unload_cog.style = disnake.ButtonStyle.red if self.cog_status else disnake.ButtonStyle.green

    @disnake.ui.button(label="Load", style=disnake.ButtonStyle.green, custom_id="load_unload_cog")
    async def load_unload_cog(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        cog_name = self.cog_name
        cog_status = self.cog_status

        button.style = disnake.ButtonStyle.red if cog_status else disnake.ButtonStyle.green
        button.label = "Unload" if cog_status else "Load"

        print(cog_status)
        if cog_status:
            self.cog_status = False
            self.bot.unload_extension(cog_name)
        else:
            self.cog_status = True
            self.bot.load_extension(cog_name)

        await interaction.response.edit_message(view=self)
        print(cog_status)