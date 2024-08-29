import secrets
import disnake
from disnake.ext import commands
from core.misc.embed import custom_embed
from core.misc.giveaway import Giveaway


class CreateModal(disnake.ui.Modal):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            title="Create new giveaway",
            custom_id="create_giveaway",
            components=[
                disnake.ui.TextInput(
                    label="Prize",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="Enter a prize",
                    max_length=100,
                    custom_id="prize",
                ),
                disnake.ui.TextInput(
                    label="Description",
                    style=disnake.TextInputStyle.paragraph,
                    required=False,
                    min_length=1,
                    max_length=200,
                    placeholder="Enter a description",
                    custom_id="description",
                ),
                disnake.ui.TextInput(
                    label="Winners",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="1",
                    custom_id="winners",
                ),
                disnake.ui.TextInput(
                    label="Duration",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="1d 1h 1m 1s (1 day, 1 hour, 1 minute, 1 second)",
                    custom_id="duration",
                ),
            ],
        )
        self.bot = bot

    async def callback(self, interaction):
        prize = interaction.text_values["prize"]
        description = (
            interaction.text_values["description"]
            if interaction.text_values["description"]
            else None
        )
        winners = interaction.text_values["winners"]
        duration = interaction.text_values["duration"].lower()
        if not winners.isdigit():
            await interaction.send(
                "❌ The number of winners must be a number", ephemeral=True
            )
            return
        if int(winners) < 1:
            await interaction.send(
                "❌ The number of winners must be greater than 0", ephemeral=True
            )
            return
        
        embed = custom_embed(
            "Create giveaway",
            "Do users have to be in voice/stage channels to enter the giveaway?"
        )
        await interaction.send(embed=embed, view = GiveawaySettingsVoice(interaction, self.bot, prize, description, int(winners), duration, "no"))

class GiveawaySettingsVoice(disnake.ui.View):
    def __init__(
        self,
        interaction,
        bot: commands.bot,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        status: str
    ) -> None:
        super().__init__()
        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration
        self.status = status
        match status:
            case "any_vc":
                self.add_item(DropDownForSettingsVoice(bot, interaction, prize, description, winners, duration))
            case "any_sc":
                self.add_item(DropDownForSettingsVoice(bot, interaction, prize, description, winners, duration))
            case "specified_vc":
                self.add_item(VoiceSpecifiedSelect(bot, interaction, prize, description, winners, duration))
            case "specified_sc":
                self.add_item(StageSpecifiedSelect(bot, interaction, prize, description, winners, duration))
            case _:
                self.add_item(DropDownForSettingsVoice(bot, interaction, prize, description, winners, duration))


class DropDownForSettingsVoice(disnake.ui.StringSelect):
    def __init__(
            self, bot: commands.Bot, 
            interaction: disnake.Interaction,
            prize: str,
            description: str | None,
            winners: int,
            duration: str
        ) -> None:
        super().__init__(
            placeholder="Choose an option",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(
                    label="No",
                    description="User not need to be in voice channel",
                    value="no",
                    emoji="❌",
                ),
                disnake.SelectOption(
                    label="Yes, In any voice channel",
                    description="User need to be in any voice channel",
                    value="any_vc",
                    emoji="🔊",
                ),
                disnake.SelectOption(
                    label="Yes, In any stage channel",
                    description="User need to be in a stage channel",
                    value="any_sc",
                    emoji="🎙",
                ),
                disnake.SelectOption(
                    label="Yes, In specified voice channel",
                    description="User need to be in specified voice channel",
                    value="specified_vc",
                    emoji="🔊",
                ),
                disnake.SelectOption(
                    label="Yes, In specified stage channel",
                    description="User need to be in specified stage channel",
                    value="specified_sc",
                    emoji="🎙",
                ),
                disnake.SelectOption(
                    label="Yes, In specified category",
                    description="User need to be in specified category (works for voice and stage channels)",
                    value="specified_cg",
                    emoji="📁",
                ),
            ],
        )
        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        selected_option = self.values[0]
        await interaction.response.defer(ephemeral=True)

        match selected_option:
            case "no":
                await self.interaction.delete_original_response()
            case "specified_vc":
                embed = custom_embed(
                    "Specify the voice channel",
                    "Please choose the voice channel you want to require in giveaway",
                )
                await self.interaction.edit_original_response(
                    embed=embed,
                    view=GiveawaySettingsVoice(
                        self.interaction, self.bot, self.prize, self.description, self.winners, self.duration, "specified_vc"
                    ),
                )
            case "specified_sc":
                embed = custom_embed(
                    "Specify the stage channel",
                    "Please choose the stage channel you want to require in giveaway",
                )
                await self.interaction.edit_original_response(
                    embed=embed,
                    view=GiveawaySettingsVoice(
                        self.interaction, self.bot, self.prize, self.description, self.winners, self.duration, "specified_sc"
                    ),
                )
            case _:
                print("gay")

class VoiceSpecifiedSelect(disnake.ui.ChannelSelect):
    def __init__(
            self, bot: commands.Bot, 
            interaction: disnake.Interaction,
            prize: str,
            description: str | None,
            winners: int,
            duration: str
        ) -> None:
        super().__init__(
            placeholder="Choose an voice",
            min_values=1,
            channel_types=[disnake.ChannelType.voice],
            max_values=1,
        )
        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        selected_option = self.values[0]
        print(type(selected_option))
        await interaction.response.defer(ephemeral=True)
        await Giveaway(self.bot).create(
            interaction, self.prize, self.description, self.winners, self.duration, selected_option
        )


class StageSpecifiedSelect(disnake.ui.ChannelSelect):
    def __init__(
            self, bot: commands.Bot, 
            interaction: disnake.Interaction,
            prize: str,
            description: str | None,
            winners: int,
            duration: str
        ) -> None:
        super().__init__(
            placeholder="Choose an stage",
            min_values=1,
            channel_types=[disnake.ChannelType.stage_voice],
            max_values=1,
        )
        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        selected_option = self.values[0]
        print(type(selected_option))
        await interaction.response.defer(ephemeral=True)
        await Giveaway(self.bot).create(
            interaction, self.prize, self.description, self.winners, self.duration, selected_option
        )