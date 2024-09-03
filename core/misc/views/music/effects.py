import disnake
import wavelink
from disnake.ext import commands


class EffectsDropdown(disnake.ui.Select):
    positive_emoji = disnake.PartialEmoji(name="🟢")
    negative_emoji = disnake.PartialEmoji(name="🔴")
    reset_emoji = disnake.PartialEmoji(name="🔄")

    def __init__(self, bot: commands.Bot, player: wavelink.Player) -> None:
        super().__init__(
            placeholder="Effects controls",
            min_values=1,
            max_values=1,
            options=list(self.generate_options()),
        )
        self.bot = bot
        self.player = player
        self.selected_states = {option.value: False for option in self.options}

    def generate_options(self):
        filter_options = [
            ("Equalizer", "The Equalizer filter to apply to the player", "equalizer"),
            ("Karaoke", "The Karaoke filter to apply to the player", "karaoke"),
            ("Timescale", "The Timescale filter to apply to the player", "timescale"),
            ("Tremolo", "The Tremolo filter to apply to the player", "tremolo"),
            ("Vibrato", "The Vibrato filter to apply to the player", "vibrato"),
            ("Rotation", "The Rotation filter to apply to the player", "rotation"),
            (
                "Distortion",
                "The Distortion filter to apply to the player",
                "distortion",
            ),
            ("Low Pass", "The Low Pass filter to apply to the player", "low_pass"),
        ]

        for label, description, value in filter_options:
            yield disnake.SelectOption(
                emoji=self.negative_emoji,
                label=label,
                description=description,
                value=value,
            )

        yield disnake.SelectOption(
            emoji=self.reset_emoji,
            label="Reset",
            description="Reset all filters that were not specified.",
            value="reset",
        )

    async def callback(self, interaction: disnake.Interaction) -> None:
        selected_option = self.values[0]
        if selected_option == "reset":
            await self.reset_filters(interaction)
        else:
            await self.toggle_filter(selected_option, interaction)

    async def reset_filters(self, interaction: disnake.Interaction) -> None:
        self.player.filters.reset()
        self.update_option_emojis(reset=True)
        await interaction.response.edit_message(view=self.view)

    async def toggle_filter(
        self, selected_option: str, interaction: disnake.Interaction
    ) -> None:
        self.selected_states[selected_option] = not self.selected_states[
            selected_option
        ]
        self.update_option_emojis(selected_option)
        await interaction.response.edit_message(view=self.view)

    def update_option_emojis(
        self, selected_option: str = None, reset: bool = False
    ) -> None:
        for option in self.options:
            if reset or option.value == selected_option:
                option.emoji = (
                    self.positive_emoji
                    if self.selected_states[option.value]
                    else self.negative_emoji
                )
