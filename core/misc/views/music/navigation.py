from typing import cast, Union

import disnake
import wavelink
from disnake.ext import commands

from core.misc.color import BasicColors
from core.misc.embed import custom_embed
from core.misc.views.music.download import DownloadDropdown
from core.misc.views.music.effects import EffectsDropdown
from core.misc.views.music.shuffle import ShuffleView


class NavigationDropdown(disnake.ui.Select):
    def __init__(
        self,
        bot: commands.Bot,
        interaction: Union[disnake.Interaction, disnake.WebhookMessage],
    ) -> None:
        super().__init__(
            placeholder="Music controls",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(
                    emoji="<:volume:1279835253577351262>",
                    label="Volume",
                    description="Change the music volume (> 1 minute)",
                    value="volume",
                ),
                disnake.SelectOption(
                    emoji="<:shuffle:1279835431315308605>",
                    label="Shuffle",
                    description="Shuffles your music queue",
                    value="shuffle",
                ),
                disnake.SelectOption(
                    emoji="<:microphone:1280556431690567835>",
                    label="Effects",
                    description="Apply effects to your music",
                    value="effects",
                ),
                disnake.SelectOption(
                    emoji="<:download:1279837205241659554>",
                    label="Download",
                    description="Download current music in any format",
                    value="download",
                ),
                disnake.SelectOption(
                    emoji="<:disconnect:1279835624257486868>",
                    label="Disconnect",
                    description="Force-disconnect from the voice channel",
                    value="disconnect",
                ),
            ],
        )
        self.interaction: disnake.Interaction = interaction
        self.bot = bot

    async def _edit_view(
        self, embed: disnake.Embed = None, clear_view: bool = False
    ) -> None:
        if embed:
            (
                await self.interaction.edit_original_response(
                    embed=embed, view=self.view
                )
                if isinstance(self.interaction, disnake.Interaction)
                else await self.interaction.edit(
                    embed=embed, view=None if clear_view else self.view
                )
            )
        else:
            (
                await self.interaction.edit_original_response(
                    view=None if clear_view else self.view
                )
                if isinstance(self.interaction, disnake.Interaction)
                else await self.interaction.edit(view=None if clear_view else self.view)
            )

    async def volume_change(self, interaction: disnake.Interaction) -> None:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        modal = disnake.ui.Modal(
            title="Enter the volume",
            custom_id="volume",
            components=[
                disnake.ui.TextInput(
                    label="New volume:",
                    custom_id="new_volume",
                    style=disnake.TextInputStyle.short,
                )
            ],
        )
        await interaction.response.send_modal(modal=modal)
        response_modal: disnake.ModalInteraction = await self.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == "volume" and i.user == interaction.user,
        )
        new_volume = int(response_modal.text_values.get("new_volume", 0))

        volume = min(100, max(1, new_volume))

        await player.set_volume(volume)
        await response_modal.send(
            embed=custom_embed(title=f"Set volume to {volume}"),
            ephemeral=True,
        )

        embed = None

        if isinstance(self.interaction, disnake.Interaction):
            embed = (await self.interaction.original_response()).embeds[0]
        elif isinstance(self.interaction, disnake.WebhookMessage):
            embed = self.interaction.embeds[0]

        embed.set_footer(text=f"Volume: {volume}% // Synth Music 2024")

        await self._edit_view(embed=embed)

    async def callback(self, interaction: disnake.Interaction) -> None:
        selected_option = self.values[0]
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        match selected_option:
            case "volume":
                await self.volume_change(interaction)
            case "shuffle":
                if not hasattr(player, "previous_queue"):
                    player.previous_queue = player.queue.copy()
                if not hasattr(player, "previous_auto_queue"):
                    player.previous_auto_queue = player.auto_queue.copy()

                if player.queue.is_empty and player.auto_queue.is_empty:
                    embed = custom_embed(
                        title="There are no songs in the queue yet",
                        color=BasicColors.ERROR,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True,
                    )

                    await self._edit_view()

                    return
                elif player.queue.is_empty and not player.auto_queue.is_empty:
                    player.auto_queue.shuffle()
                else:
                    player.queue.shuffle()

                track: wavelink.Playable = player.current
                next_song = (
                    player.queue[0]
                    if not player.queue.is_empty
                    else player.auto_queue[0]
                )

                embed = custom_embed(
                    title="Shuffled the queue",
                    description=f"Current song: **{track.title}**\nNext song: **{next_song.title}**",
                    color=BasicColors.SUCCESS,
                )

                await interaction.response.send_message(
                    embed=embed,
                    view=ShuffleView(
                        self.bot,
                        interaction,
                        player.previous_queue,
                        player.previous_auto_queue,
                    ),
                    ephemeral=True,
                )

                await self._edit_view()

            case "effects":
                embed = custom_embed(title="Adjust the track effects")
                await interaction.response.send_message(embed=embed, ephemeral=True)

                view = disnake.ui.View()
                view.add_item(EffectsDropdown(self.bot, player, interaction))
                await interaction.edit_original_response(embed=embed, view=view)

                await self._edit_view()

            case "download":
                embed = custom_embed(
                    title="Download a track",
                    description="Choose an format for downloading a track",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

                view = disnake.ui.View()
                view.add_item(DownloadDropdown(self.bot))
                await interaction.edit_original_response(embed=embed, view=view)

                await self._edit_view()

            case "disconnect":
                await player.disconnect()

                embed = custom_embed(
                    title=f"Disconnected from voice channel",
                    color=disnake.Colour.red(),
                )
                await self._edit_view(embed=embed, clear_view=True)
