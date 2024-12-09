from typing import Optional
import disnake
import wavelink
from disnake.ext import commands

from core.misc.embed import CustomEmbed


class EffectsDropdown(disnake.ui.Select):
    positive_emoji = disnake.PartialEmoji(name="checkmark", id=1282338829486788670)
    negative_emoji = disnake.PartialEmoji(name="crossmark", id=1282338837456224394)
    reset_emoji = disnake.PartialEmoji(name="reset", id=1282736680201355314)

    FILTERS = {
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
        self.bot: commands.Bot = bot
        self.player: wavelink.Player = player
        self.interaction: disnake.Interaction = interaction

        self.filters: wavelink.Filters = player.filters

        super().__init__(
            placeholder="Adjust effects",
            min_values=1,
            max_values=1,
            options=list(self.generate_options()),
        )

        self.selected_states: dict = {option.value: False for option in self.options}

    def generate_options(self):
        filter_options = list(self.FILTERS.keys())
        for label in filter_options:
            yield disnake.SelectOption(
                emoji=self.negative_emoji if not self.filters().get(label) else self.positive_emoji,  # type: ignore
                label=label.capitalize(),
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

            description = "\n".join(
                f"{EffectsDropdown.positive_emoji if self.player.filters().get(effect) else EffectsDropdown.negative_emoji} {effect.capitalize()}"
                # type: ignore
                for effect in [
                    "timescale",
                    "rotation",
                    "tremolo",
                    "vibrato",
                    "equalizer",
                ]
            )
            embed = CustomEmbed(
                title="Adjust the track effects",
                description=description,
            ).get_embed()

            embed.set_author(
                name=self.interaction.user.display_name,
                icon_url=self.interaction.user.display_avatar.url,
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
        if self.filters().get(selected_option):  # type: ignore
            getattr(self.filters, selected_option).reset()
            self.selected_states[selected_option] = False
        else:
            filter_func = self.FILTERS[selected_option]
            filter_func(self.filters)
            self.selected_states[selected_option] = True

        await self.player.set_filters(self.filters)

        description = "\n".join(
            f"{EffectsDropdown.positive_emoji if self.player.filters().get(effect) else EffectsDropdown.negative_emoji} {effect.capitalize()}"  # type: ignore
            for effect in ["timescale", "rotation", "tremolo", "vibrato", "equalizer"]
        )
        embed = CustomEmbed(
            title="Track Filters",
            description=description,
        ).get_embed()

        embed.set_author(
            name=self.interaction.user.display_name,
            icon_url=self.interaction.user.display_avatar.url,
        )

        await self.interaction.edit_original_response(embed=embed)

        self.update_option_emojis(selected_option)

        await interaction.response.edit_message(view=self.view)

    def update_option_emojis(
        self, selected_option: Optional[str] = None, reset: bool = False
    ) -> None:
        for option in self.options:
            if reset and option.value == "reset":
                continue

            if reset or option.value == selected_option:
                option.emoji = (
                    self.positive_emoji
                    if self.selected_states.get(option.value, False)
                    else self.negative_emoji
                )
