import disnake
import wavelink
from disnake.ext import commands

from core.misc.embed import custom_embed


class EffectsDropdown(disnake.ui.Select):
    positive_emoji = disnake.PartialEmoji(name="🟢")
    negative_emoji = disnake.PartialEmoji(name="🔴")
    reset_emoji = disnake.PartialEmoji(name="🔄")

    FILTERS = {
        "equalizer": lambda f: f.equalizer,
        "timescale": lambda f: f.timescale.set(pitch=1.2, speed=1.1, rate=1),
        "tremolo": lambda f: f.tremolo.set(depth=0.5, frequency=2.0),
        "vibrato": lambda f: f.vibrato.set(depth=0.5, frequency=2.0),
        "rotation": lambda f: f.rotation.set(rotation_hz=0.2),
    }

    def __init__(
        self,
        bot: commands.Bot,
        player: wavelink.Player,
        interaction: disnake.Interaction,
    ) -> None:
        super().__init__(
            placeholder="Effects controls",
            min_values=1,
            max_values=1,
            options=list(self.generate_options()),
        )
        self.bot: commands.Bot = bot
        self.player: wavelink.Player = player
        self.interaction: disnake.Message = interaction

        self.filters: wavelink.Filters = player.filters
        self.selected_states: dict = {option.value: False for option in self.options}

    def generate_options(self):
        filter_options = list(self.FILTERS.keys())
        for label in filter_options:
            yield disnake.SelectOption(
                emoji=self.negative_emoji,
                label=label.capitalize(),
                description=f"The {label.capitalize()} filter to apply to the player",
                value=label,
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

            embed = custom_embed(
                title="Adjust the track effects",
                description="All filters have been disabled or set to default",
            )
            await self.interaction.edit_original_response(embed=embed)
        else:
            await self.toggle_filter(selected_option, interaction)

    async def reset_filters(self, interaction: disnake.Interaction) -> None:
        self.filters.reset()
        self.selected_states = {key: False for key in self.selected_states}
        self.update_option_emojis(reset=True)
        await self.player.set_filters(self.filters)
        await interaction.response.edit_message(view=self.view)

    async def toggle_filter(
        self, selected_option: str, interaction: disnake.Interaction
    ) -> None:
        self.selected_states[selected_option] = not self.selected_states[
            selected_option
        ]

        filter_func = self.FILTERS[selected_option]

        if self.selected_states[selected_option]:
            filter_func(self.filters)
            status = "Enabled"
        else:
            getattr(self.filters, selected_option).reset()
            status = "Disabled"

        await self.player.set_filters(self.filters)

        embed = custom_embed(
            title="Adjust the track effects",
            description=f"**{status} filter:** `{selected_option.capitalize()}``.\n**Enabled filters:** {', '.join([key.capitalize() for key, val in self.selected_states.items() if val]) or 'None'}",
        )

        await self.interaction.edit_original_response(embed=embed)

        self.update_option_emojis(selected_option)

        await interaction.response.edit_message(view=self.view)

    def update_option_emojis(
        self, selected_option: str = None, reset: bool = False
    ) -> None:
        for option in self.options:
            if reset or option.value == selected_option:
                option.emoji = (
                    self.positive_emoji
                    if self.selected_states.get(option.value, False)
                    else self.negative_emoji
                )
