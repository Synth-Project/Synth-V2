import disnake
from disnake.ext import commands
from core.misc.embed import custom_embed
from core.misc.views.giveaways.voice import GiveawaySettingsVoice


class GiveawaySettingsChannel(disnake.ui.View):
    def __init__(
        self,
        interaction,
        bot: commands.bot,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        status: bool,
    ) -> None:
        super().__init__()

        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration
        if status:
            self.add_item(
                GiveawayChannelSelect(
                    bot,
                    interaction,
                    self.prize,
                    self.description,
                    self.winners,
                    self.duration,
                )
            )
        else:
            self.add_item(
                GiveawayChannelYes(
                    bot,
                    interaction,
                    self.prize,
                    self.description,
                    self.winners,
                    self.duration,
                )
            )
            self.add_item(
                GiveawayChannelNo(
                    bot,
                    interaction,
                    self.prize,
                    self.description,
                    self.winners,
                    self.duration,
                )
            )


class GiveawayChannelYes(disnake.ui.Button):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
    ) -> None:
        super().__init__(label="Yes", style=disnake.ButtonStyle.green, custom_id="yes")

        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.defer(ephemeral=True)

        embed = custom_embed(
            title="Create giveaway",
            description=f"{self.description}\n- Prize: **{self.prize}**\n- Winners: **{self.winners}**\n- Channel: {interaction.channel.mention}\nChange the channel",
        )
        await self.interaction.edit_original_response(
            embed=embed,
            view=GiveawaySettingsChannel(
                interaction,
                self.bot,
                self.prize,
                self.description,
                int(self.winners),
                self.duration,
                True,
            ),
        )


class GiveawayChannelNo(disnake.ui.Button):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
    ) -> None:
        super().__init__(label="No", style=disnake.ButtonStyle.red, custom_id="no")

        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.defer(ephemeral=True)

        embed = custom_embed(
            title="Create giveaway",
            description=f"{self.description}\n- Prize: **{self.prize}**\n- Winners: **{self.winners}**\n- Channel: {interaction.channel.mention}\nDo users have to be in voice/stage channels to enter the giveaway?",
        )
        await self.interaction.edit_original_response(
            embed=embed,
            view=GiveawaySettingsVoice(
                interaction,
                self.bot,
                self.prize,
                self.description,
                int(self.winners),
                self.duration,
                "no",
                interaction.channel,
            ),
        )


class GiveawayChannelSelect(disnake.ui.ChannelSelect):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: disnake.Interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
    ) -> None:
        super().__init__(
            placeholder="Choose an channel",
            min_values=1,
            channel_types=[
                disnake.ChannelType.voice,
                disnake.ChannelType.text,
                disnake.ChannelType.forum,
            ],
            max_values=1,
        )

        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.defer(ephemeral=True)

        embed = custom_embed(
            title="Create giveaway",
            description=f"{self.description}\n- Prize: **{self.prize}**\n- Winners: **{self.winners}**\n- Channel: {interaction.channel.mention}\nDo users have to be in voice/stage channels to enter the giveaway?",
        )
        await self.interaction.edit_original_response(
            embed=embed,
            view=GiveawaySettingsVoice(
                interaction,
                self.bot,
                self.prize,
                self.description,
                int(self.winners),
                self.duration,
                "no",
                self.values[0],
            ),
            ephemeral=True,
        )
