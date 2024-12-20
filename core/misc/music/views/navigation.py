from typing import cast, Union, Optional

import disnake
import importlib
import wavelink
from disnake.ext import commands

from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed
from core.misc.misc import check_user_role
from core.misc.music.views.download import DownloadDropdown
from core.misc.music.views.effects import EffectsDropdown
from core.misc.music.views.shuffle import ShuffleView

from core.database.repositories.guild import GuildMusicRepository


class NavigationDropdown(disnake.ui.Select):
    """
    Navigation dropdown menu class for music player
    :disnake.ui.Select:
    """

    def __init__(
        self,
        bot: commands.Bot,
        player: Optional[wavelink.Player],
        interaction: Union[disnake.Interaction, disnake.Message],
    ) -> None:
        self.interaction: Union[disnake.Interaction, disnake.Message] = interaction
        self.bot = bot
        self.player = player
        self.functions = getattr(
            importlib.import_module("core.misc.music.functions"), "MusicFunctions"
        )
        self.guild_music_repo = GuildMusicRepository()

        self.queue_ = (
            player.queue  # type: ignore
            if not player.queue.is_empty  # type: ignore
            else (
                player.auto_queue  # type: ignore
                if player.autoplay == wavelink.AutoPlayMode.enabled  # type: ignore
                else player.queue  # type: ignore
            )
        )

        options = [
            disnake.SelectOption(
                emoji="<:volume:1279835253577351262>",
                label="Volume",
                description="Change the music volume",
                value="volume",
            ),
            disnake.SelectOption(
                emoji="<:filter:1284445407337779251>",
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
                emoji="<:microphone:1280556431690567835>",
                label="Lyrics",
                description="View the current song lyrics",
                value="lyrics",
            ),
            disnake.SelectOption(
                emoji="<:disconnect:1279835624257486868>",
                label="Disconnect",
                description="Disconnect from the voice channel",
                value="disconnect",
            ),
        ]

        if len(self.queue_) >= 1:
            options.insert(
                1,
                disnake.SelectOption(
                    emoji="<:shuffle:1279835431315308605>",
                    label="Shuffle",
                    description="Shuffle the current queue",
                    value="shuffle",
                ),
            )

        super().__init__(
            placeholder="Music controls",
            min_values=1,
            max_values=1,
            options=options,
        )

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

        if clear_view:
            (
                await self.player.main_message.edit(embed=embed, view=None)  # type: ignore
                if embed
                else await self.player.main_message.edit(view=None)  # type: ignore
            )
        else:
            self.options = [
                disnake.SelectOption(
                    emoji=opt.emoji,
                    label=opt.label,
                    description=opt.description,
                    value=opt.value,
                )
                for opt in self.options
            ]

            (
                await self.player.main_message.edit(embed=embed, view=self.view)  # type: ignore
                if embed
                else await self.player.main_message.edit(view=self.view)  # type: ignore
            )

    @staticmethod
    async def _get_lyrics(node: wavelink.Node, guild_id: int) -> Optional[str]:
        """
        Get the lyrics of the player

        Parameters:
        node: wavelink.Node
            The node to send the request to
        guild_id: int
            The guild id to send the request to

        Returns: str
            The lyrics of the player
        """
        try:
            result = await node.send(
                method="GET",
                path=f"v4/sessions/{node.session_id}/players/{guild_id}/lyrics",
            )
            lyrics = [line["line"] for line in result["lines"]]
            return "\n".join(lyrics)
        except BaseException:
            return None

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
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        response_modal = await self._send_modal(
            interaction, "Enter the volume", "volume", "New volume:"
        )
        new_volume = int(response_modal.text_values.get("input_value", "0"))
        volume = min(100, max(1, new_volume))

        embed = await self.functions.check_error_volume(interaction, volume)

        await response_modal.send(
            embed=embed,
            ephemeral=True,
        )

        embed = player.main_message.embeds[0]  # type: ignore
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
        if not hasattr(player, "previous_queue"):
            player.previous_queue = player.queue.copy()  # type: ignore
        if not hasattr(player, "previous_auto_queue"):
            player.previous_auto_queue = player.auto_queue.copy()  # type: ignore

        (player.auto_queue if player.queue.is_empty else player.queue).shuffle()
        next_song = (
            player.queue[0] if not player.queue.is_empty else player.auto_queue[0]
        )

        embed = CustomEmbed(
            title="<:shuffle:1279835431315308605> Shuffled the queue",
            description=f"Current song: **{player.current.title}**\nNext song: **{next_song.title}**",  # type: ignore
            color=BasicColors.SUCCESS,
        ).get_embed()
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
            view=ShuffleView(
                self.bot,
                interaction,
                player.previous_queue,  # type: ignore
                player.previous_auto_queue,  # type: ignore
            ),
        )

        await self._edit_view()

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

        description = "\n".join(
            f"{EffectsDropdown.positive_emoji if player.filters().get(effect) else EffectsDropdown.negative_emoji} {effect.capitalize()}"  # type: ignore
            for effect in ["timescale", "rotation", "tremolo", "vibrato", "equalizer"]
        )

        embed = CustomEmbed(
            title="<:filter:1284445407337779251> Adjust the track filters",
            description=description,
        ).get_embed()
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(
            embed=embed,
            view=disnake.ui.View().add_item(
                EffectsDropdown(self.bot, player, interaction)
            ),
            ephemeral=True,
        )
        await self._edit_view()

    async def handle_download(self, interaction: disnake.Interaction) -> None:
        """
        Handle the download of the player

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to

        Returns: None
        """
        embed = CustomEmbed(
            title="<:download:1279837205241659554> Download a track",
            description="Choose the track output format (up to 25mb)",
        ).get_embed()

        await interaction.response.send_message(
            embed=embed,
            view=disnake.ui.View().add_item(DownloadDropdown(self.bot)),
            ephemeral=True,
        )
        await self._edit_view()

    async def handle_lyrics(self, interaction: disnake.Interaction) -> None:
        """
        Get the lyrics of the player

        Parameters:
        interaction: disnake.Interaction

        Returns: None
        """

        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        lyrics = await self._get_lyrics(player.node, player.guild.id)  # type: ignore

        embed = CustomEmbed(
            author=interaction.user,
            title=(
                f"Lyrics for {player.current.title}"  # type: ignore
                if lyrics
                else f"<:crossmark:1282338837456224394> Could not find lyrics for {player.current.title}"  # type: ignore
            ),
            description=f"```{lyrics}```" if lyrics else "",
            embed_type="default" if lyrics else "error",
        ).get_embed()

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self._edit_view()

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
        await self.functions.disconnect(interaction)

    async def callback(self, interaction: disnake.Interaction) -> None:
        """
        The callback for the view

        Parameters:
        interaction: disnake.Interaction
            The interaction to send the modal to

        Returns: None
        """
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

        option_actions = {
            "volume": self.volume_change,
            "shuffle": lambda i: self.shuffle_queue(i, player),
            "effects": lambda i: self.handle_effects(i, player),
            "download": self.handle_download,
            "lyrics": self.handle_lyrics,
            "disconnect": lambda i: self.handle_disconnect(i, player),
        }

        action = option_actions.get(self.values[0])

        dj_role = await self.guild_music_repo.find_dj_role(
            guild_id=self.interaction.guild.id
        )

        if self.values[0] == "effects":
            if not check_user_role(
                self.interaction.guild, self.interaction.user, dj_role
            ):
                await self._edit_view()
                return await interaction.response.send_message(
                    "You must have a DJ role to use this function", ephemeral=True
                )

            if not dj_role:
                await self._edit_view()
                return await interaction.response.send_message(
                    "You must be or set a DJ role to use this function", ephemeral=True
                )

        if action:
            await action(interaction)
