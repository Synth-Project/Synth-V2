from typing import cast

import asyncio, io

import disnake
from disnake.ext import commands
import wavelink

from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed
from core.misc.misc import download_track

# ! Max file size (25MB)
MAX_FILE_SIZE_MB = 25 * 1024 * 1024


class DownloadDropdown(disnake.ui.Select):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(
            placeholder="Choose a format",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(
                    emoji="<:download:1279837205241659554>",
                    label="MP3 Format",
                    description="Download current music in mp3 format",
                    value="mp3",
                ),
                disnake.SelectOption(
                    emoji="<:download:1279837205241659554>",
                    label="OGG Format",
                    description="Download current music in ogg format",
                    value="ogg",
                ),
                disnake.SelectOption(
                    emoji="<:download:1279837205241659554>",
                    label="WAV Format",
                    description="Download current music in wav format",
                    value="wav",
                ),
                disnake.SelectOption(
                    emoji="<:download:1279837205241659554>",
                    label="FLAC Format",
                    description="Download current music in flac format",
                    value="flac",
                ),
            ],
        )
        self.bot = bot

    @staticmethod
    async def download_track(
        interaction: disnake.Interaction, audio_format: str
    ) -> None:
        """
        Download the current track
        Parameters:
        interaction: disnake.Interaction
            The interaction that triggered the download
        audio_format: str
            The format to download the track in

        Returns: None
        """
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

        if not player or not player.current:
            embed = CustomEmbed(
                title="<:crossmark:1282338837456224394> There are no songs in the queue yet",
                color=BasicColors.ERROR,
            ).get_embed()
            return await interaction.response.edit_message(embed=embed, view=None)

        track = player.current

        await interaction.response.edit_message(
            content="<a:loading:1168599537682755584> Downloading track, please wait...",
            embed=None,
            view=None,
        )

        try:
            with io.BytesIO() as output:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: download_track(track, output)
                )
                output.seek(0)

                file_size = output.getbuffer().nbytes

                if file_size > MAX_FILE_SIZE_MB:
                    await interaction.edit_original_response(
                        content=f"Error: Track exceeds the 25MB limit (size: {file_size / (1024 * 1024):.2f} MB)."
                    )
                    return

                await interaction.edit_original_response(
                    content=f"Here is the track in {audio_format} format",
                    file=disnake.File(output, f"{track.title}.{audio_format}"),
                )
        except ValueError:
            await interaction.edit_original_response("Internal server error or no videos found for this track.")

    async def callback(self, interaction: disnake.Interaction) -> None:
        await self.download_track(interaction, self.values[0])
