import asyncio
import io
from typing import cast

import disnake
import wavelink
from disnake.ext import commands

from core.misc.embed import custom_embed
from core.misc.misc import download_track
from core.misc.views.music.effects import EffectsDropdown


class NavigationDropdown(disnake.ui.Select):
    def __init__(self, bot: commands.Bot) -> None:
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
                    description="Download current music in mp3 format",
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
        self.bot = bot

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
        await response_modal.response.send_message(
            embed=custom_embed(title=f"Set volume to {volume}"),
            ephemeral=True,
        )

    @staticmethod
    async def download_track(
        interaction: disnake.Interaction, audio_format: str = "mp3"
    ) -> None:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player.current:
            embed = custom_embed(
                title="There are no songs in the queue yet",
                color=disnake.Color.red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        track: wavelink.Playable = player.current

        await interaction.response.send_message(
            "Downloading track, please wait...", ephemeral=True
        )

        with io.BytesIO() as output:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: download_track(track, output)
            )
            output.seek(0)

            file_size = output.getbuffer().nbytes
            max_size = 25 * 1024 * 1024  # 25 MB

            if file_size > max_size:
                await interaction.edit_original_response(
                    content=f"Error: The track exceeds the 25MB limit (size: {file_size / (1024 * 1024):.2f} MB).",
                    ephemeral=True,
                )
                return

            await interaction.edit_original_response(
                content="Here is the track in mp3 format",
                file=disnake.File(output, f"{track.title}.{audio_format}"),
            )

    async def callback(self, interaction: disnake.Interaction) -> None:
        selected_option = self.values[0]
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        match selected_option:
            case "volume":
                await self.volume_change(interaction)
            case "shuffle":
                if player.queue.is_empty and player.auto_queue.is_empty:
                    embed = custom_embed(
                        title="There are no songs in the queue yet",
                        color=disnake.Color.red(),
                    )
                    return await interaction.response.send_message(
                        embed=embed, ephemeral=True
                    )
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
                    color=disnake.Colour.green(),
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

            case "effects":
                embed = custom_embed(title="Adjust the track effects")
                await interaction.response.send_message(embed=embed, ephemeral=True)

                view = disnake.ui.View()
                view.add_item(EffectsDropdown(self.bot, player, interaction))
                await interaction.edit_original_response(embed=embed, view=view)

            case "download":
                await self.download_track(interaction, "ogg")

            case "disconnect":
                await player.disconnect()

                embed = custom_embed(
                    title=f"Disconnected from voice channel",
                    color=disnake.Colour.red(),
                )
                await interaction.response.edit_message(embed=embed, view=None)
