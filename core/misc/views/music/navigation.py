from typing import cast, Union, Optional

import disnake
from disnake.ext import commands
import wavelink

from core.misc.color import BasicColors
from core.misc.embed import custom_embed

from core.misc.views.music.download import DownloadDropdown
from core.misc.views.music.effects import EffectsDropdown
from core.misc.views.music.shuffle import ShuffleView


class NavigationDropdown(disnake.ui.Select):
    """
    Navigation dropdown menu class for music player
    :disnake.ui.Select:
    """

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
                    description="Change the music volume",
                    value="volume",
                ),
                disnake.SelectOption(
                    emoji="<:shuffle:1279835431315308605>",
                    label="Shuffle",
                    description="Shuffle your music queue",
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
                    description="Download the current track",
                    value="download",
                ),
                disnake.SelectOption(
                    emoji="<:disconnect:1279835624257486868>",
                    label="Disconnect",
                    description="Disconnect from the voice channel",
                    value="disconnect",
                ),
            ],
        )
        self.interaction: disnake.Interaction = interaction
        self.bot = bot

    async def _edit_view(
        self, embed: Optional[disnake.Embed] = None, clear_view: bool = False
    ) -> None:
        """
        Edit the entered view

        Parameters:
        embed: Optional[disnake.Embed]
            The embed to send
        clear_view: bool
            Whether to clear the view

        Returns: None
        """
        edit_func = (
            self.interaction.edit_original_response
            if isinstance(self.interaction, disnake.Interaction)
            else self.interaction.edit
        )
        await edit_func(embed=embed, view=None if clear_view else self.view)

    async def _send_modal(
        self, interaction: disnake.Interaction, title: str, custom_id: str, label: str
    ) -> disnake.ModalInteraction:
        """
        Send a modal to the user

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to
        title: str
            The title of the modal
        custom_id: str
            The custom id of the modal
        label: str
            The label of the modal

        Returns: disnake.ModalInteraction
            The modal interaction
        """
        modal = disnake.ui.Modal(
            title=title,
            custom_id=custom_id,
            components=[
                disnake.ui.TextInput(
                    label=label,
                    custom_id="input_value",
                    style=disnake.TextInputStyle.short,
                )
            ],
        )
        await interaction.response.send_modal(modal)
        return await self.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == custom_id and i.user == interaction.user,
        )

    async def volume_change(self, interaction: disnake.Interaction) -> None:
        """
        Change the volume of the player

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to

        Returns: None
        """
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        response_modal = await self._send_modal(
            interaction, "Enter the volume", "volume", "New volume:"
        )
        new_volume = int(response_modal.text_values.get("input_value", "0"))
        volume = min(100, max(1, new_volume))

        await player.set_volume(volume)
        await response_modal.send(
            embed=custom_embed(title=f"<:checkmark:1282338829486788670> Set volume to {volume}"), ephemeral=True
        )

        embed = (await self.interaction.original_response()).embeds[0]
        embed.set_footer(text=f"Volume: {volume}% // Synth Music 2024")
        await self._edit_view(embed=embed)

    async def shuffle_queue(
        self, interaction: disnake.Interaction, player: wavelink.Player
    ) -> None:
        """
        Shuffle the queue

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to
        player: wavelink.Player
            The player to shuffle

        Returns: None
        """
        if player.queue.is_empty and player.auto_queue.is_empty:
            embed = custom_embed(title="<:crossmark:1282338837456224394> No songs in the queue", color=BasicColors.ERROR)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # TODO: Make the shuffle removed if not queue found

        if not hasattr(player, "previous_queue"):
            player.previous_queue = player.queue.copy()
        if not hasattr(player, "previous_auto_queue"):
            player.previous_auto_queue = player.auto_queue.copy()

        (player.auto_queue if player.queue.is_empty else player.queue).shuffle()
        next_song = (
            player.queue[0] if not player.queue.is_empty else player.auto_queue[0]
        )

        embed = custom_embed(
            title="<:shuffle:1279835431315308605> Shuffled the queue",
            description=f"Current song: **{player.current.title}**\nNext song: **{next_song.title}**",
            color=BasicColors.SUCCESS,
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
            view=ShuffleView(
                self.bot, interaction, player.previous_queue, player.previous_auto_queue
            ),
        )

    async def handle_effects(
        self, interaction: disnake.Interaction, player: wavelink.Player
    ) -> None:
        """
        Handle the effects of the player

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to
        player: wavelink.Player
            The player to handle effects for

        Returns: None
        """
        embed = custom_embed(
            title="<:microphone:1280556431690567835> Adjust the track effects", description="**Filters enabled:** TODO"
        )
        await interaction.response.send_message(
            embed=embed,
            view=disnake.ui.View().add_item(
                EffectsDropdown(self.bot, player, interaction)
            ),
            ephemeral=True,
        )

    async def handle_download(self, interaction: disnake.Interaction) -> None:
        """
        Handle the download of the player

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to

        Returns: None
        """
        embed = custom_embed(
            title="<:download:1279837205241659554> Download a track",
            description="Choose the track output format (up to 25mb)",
        )

        await interaction.response.send_message(
            embed=embed,
            view=disnake.ui.View().add_item(DownloadDropdown(self.bot)),
            ephemeral=True,
        )

    async def handle_disconnect(
        self, interaction: disnake.Interaction, player: wavelink.Player
    ) -> None:
        """
        Handle the disconnect of the player

        Parameters:
        _: disnake.Interaction
            The interaction to send the modal to
        player: wavelink.Player
            The player to disconnect

        Returns: None
        """
        await player.disconnect()
        embed = custom_embed(
            author=interaction.user,
            title=f"<:disconnect:1279835624257486868> Disconnected from voice channel",
            color=BasicColors.ERROR,
        )
        await self._edit_view(embed=embed, clear_view=True)

    async def callback(self, interaction: disnake.Interaction) -> None:
        """
        The callback for the view

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to

        Returns: None
        """
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        option_actions = {
            "volume": self.volume_change,
            "shuffle": lambda i: self.shuffle_queue(i, player),
            "effects": lambda i: self.handle_effects(i, player),
            "download": self.handle_download,
            "disconnect": lambda i: self.handle_disconnect(i, player),
        }

        action = option_actions.get(self.values[0])
        if action:
            await action(interaction)
