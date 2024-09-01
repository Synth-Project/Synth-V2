import disnake
from disnake.ext import commands
from core.database.models.giveaway import VoiceEnum
from core.misc.embed import custom_embed
from core.misc.giveaway import Giveaway


class GiveawayImageSet(disnake.ui.View):
    def __init__(
        self,
        interaction,
        bot: commands.Bot,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        giveaway_channel: disnake.abc.GuildChannel,
        require_type: VoiceEnum,
        required_channel: disnake.abc.GuildChannel,
    ) -> None:
        super().__init__()

        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration
        self.giveaway_channel = giveaway_channel
        self.required_channel = required_channel
        self.require_type = require_type

    @disnake.ui.button(
        label="Yes",
        style=disnake.ButtonStyle.green,
    )
    async def yes(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        await interaction.response.send_modal(
            GiveawayImageModal(
                self.bot,
                self.interaction,
                self.prize,
                self.description,
                self.winners,
                self.duration,
                self.giveaway_channel,
                self.require_type,
                self.required_channel,
            )
        )

    @disnake.ui.button(
        label="No",
        style=disnake.ButtonStyle.red,
    )
    async def no(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        await Giveaway(self.bot).create(
            self.interaction,
            self.prize,
            self.description,
            self.winners,
            self.duration,
            self.require_type,
            self.required_channel,
            self.giveaway_channel,
            None,
        )


class GiveawayImageModal(disnake.ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        interaction,
        prize: str,
        description: str | None,
        winners: int,
        duration: str,
        giveaway_channel: disnake.abc.GuildChannel,
        require_type: VoiceEnum,
        required_channel: disnake.abc.GuildChannel,
    ):
        super().__init__(
            title="Set new Image URL",
            custom_id="set_image_giveaway",
            components=[
                disnake.ui.TextInput(
                    label="Image URL",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    min_length=1,
                    placeholder="Enter a image URL",
                    max_length=255,
                    custom_id="image",
                ),
            ],
        )
        self.bot = bot
        self.interaction = interaction
        self.prize = prize
        self.description = description
        self.winners = winners
        self.duration = duration
        self.giveaway_channel = giveaway_channel
        self.require_type = require_type
        self.required_channel = required_channel

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.defer(ephemeral=True)
        await Giveaway(self.bot).create(
            interaction,
            self.prize,
            self.description,
            self.winners,
            self.duration,
            self.require_type,
            self.required_channel,
            self.giveaway_channel,
            interaction.text_values["image"],
        )
