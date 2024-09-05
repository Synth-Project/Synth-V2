import asyncio
import io
from typing import cast
import disnake
from disnake.ext import commands
import wavelink

from core.misc.embed import custom_embed
from core.misc.misc import download_track

class DownloadDropdown(disnake.ui.Select):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(
            placeholder="Choose an format",
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
        interaction: disnake.Interaction, audio_format: str = "mp3"
    ) -> None:
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player.current:
            embed = custom_embed(
                title="There are no songs in the queue yet",
                color=disnake.Color.red(),
            )
            return await interaction.response.edit_message(embed=embed, view = None)

        track: wavelink.Playable = player.current

        await interaction.response.edit_message(
            "Downloading track, please wait...", view = None, embed = None
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
        await self.download_track(interaction, self.values[0])