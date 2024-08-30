import disnake
from disnake.ext import commands
from core.database.models.giveaways import VoiceEnum
from core.misc.embed import custom_embed
from core.misc.giveaway import Giveaway


class GiveawaySettingsVoice(disnake.ui.View):
    def __init__(
        self,
        interaction,
        bot: commands.bot,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        status: str,
        channel: disnake.abc.GuildChannel,
    ) -> None:
        super().__init__()
        match status:
            case "any_vc":
                self.add_item(
                    DropDownForSettingsVoice(
                        bot, interaction, prize, description, winners, duration, channel
                    )
                )
            case "any_sg":
                self.add_item(
                    DropDownForSettingsVoice(
                        bot, interaction, prize, description, winners, duration, channel
                    )
                )
            case "specified_vc":
                self.add_item(
                    VoiceSpecifiedSelect(
                        bot, interaction, prize, description, winners, duration, channel
                    )
                )
            case "specified_sg":
                self.add_item(
                    StageSpecifiedSelect(
                        bot, interaction, prize, description, winners, duration, channel
                    )
                )
            case "specified_cg":
                self.add_item(
                    CategorySpecifiedSelect(
                        bot, interaction, prize, description, winners, duration, channel
                    )
                )
            case _:
                self.add_item(
                    DropDownForSettingsVoice(
                        bot, interaction, prize, description, winners, duration, channel
                    )
                )


class DropDownForSettingsVoice(disnake.ui.StringSelect):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        channel: disnake.abc.GuildChannel,
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
                    value="any_sg",
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
                    value="specified_sg",
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
        self.channel = channel

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        selected_option = self.values[0]
        await interaction.response.defer(ephemeral=True)

        match selected_option:
            case "no":
                await self.interaction.delete_original_response()
                await Giveaway(self.bot).create(
                    interaction,
                    self.prize,
                    self.description,
                    self.winners,
                    self.duration,
                    VoiceEnum.NONE,
                    None,
                    self.channel,
                )
            case "any_vc":
                await self.interaction.delete_original_response()
                await Giveaway(self.bot).create(
                    interaction,
                    self.prize,
                    self.description,
                    self.winners,
                    self.duration,
                    VoiceEnum.ANY_VC,
                    None,
                    self.channel,
                )
            case "any_sg":
                await self.interaction.delete_original_response()
                await Giveaway(self.bot).create(
                    interaction,
                    self.prize,
                    self.description,
                    self.winners,
                    self.duration,
                    VoiceEnum.ANY_SG,
                    None,
                    self.channel,
                )
            case "specified_vc":
                embed = custom_embed(
                    "Specify the voice channel",
                    "Please choose the voice channel you want to require in giveaway",
                )
                await self.interaction.edit_original_response(
                    embed=embed,
                    view=GiveawaySettingsVoice(
                        self.interaction,
                        self.bot,
                        self.prize,
                        self.description,
                        self.winners,
                        self.duration,
                        selected_option,
                        self.channel,
                    ),
                )
            case "specified_sg":
                embed = custom_embed(
                    "Specify the stage channel",
                    "Please choose the stage channel you want to require in giveaway",
                )
                await self.interaction.edit_original_response(
                    embed=embed,
                    view=GiveawaySettingsVoice(
                        self.interaction,
                        self.bot,
                        self.prize,
                        self.description,
                        self.winners,
                        self.duration,
                        selected_option,
                        self.channel,
                    ),
                )
            case "specified_cg":
                embed = custom_embed(
                    "Specify the category",
                    "Please choose the category you want to require in giveaway",
                )
                await self.interaction.edit_original_response(
                    embed=embed,
                    view=GiveawaySettingsVoice(
                        self.interaction,
                        self.bot,
                        self.prize,
                        self.description,
                        self.winners,
                        self.duration,
                        selected_option,
                        self.channel,
                    ),
                )


class VoiceSpecifiedSelect(disnake.ui.ChannelSelect):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        channel: disnake.abc.GuildChannel,
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
        self.channel = channel

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await self.interaction.delete_original_response()
        selected_option = self.values[0]
        await interaction.response.defer(ephemeral=True)
        await Giveaway(self.bot).create(
            interaction,
            self.prize,
            self.description,
            self.winners,
            self.duration,
            VoiceEnum.SPECIFIED_VC,
            selected_option,
            self.channel,
        )


class StageSpecifiedSelect(disnake.ui.ChannelSelect):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        channel: disnake.abc.GuildChannel,
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
        self.channel = channel

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await self.interaction.delete_original_response()
        selected_option = self.values[0]
        await interaction.response.defer(ephemeral=True)
        await Giveaway(self.bot).create(
            interaction,
            self.prize,
            self.description,
            self.winners,
            self.duration,
            VoiceEnum.SPECIFIED_SG,
            selected_option,
            self.channel,
        )


class CategorySpecifiedSelect(disnake.ui.ChannelSelect):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        channel: disnake.abc.GuildChannel,
    ) -> None:
        super().__init__(
            placeholder="Choose an category",
            min_values=1,
            channel_types=[disnake.ChannelType.category],
            max_values=1,
        )
        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration
        self.channel = channel

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await self.interaction.delete_original_response()
        selected_option = self.values[0]
        await interaction.response.defer(ephemeral=True)
        await Giveaway(self.bot).create(
            interaction,
            self.prize,
            self.description,
            self.winners,
            self.duration,
            VoiceEnum.SPECIFIED_CG,
            selected_option,
            self.channel,
        )
