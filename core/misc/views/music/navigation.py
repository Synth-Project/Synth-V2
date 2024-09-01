import io
import asyncio

import disnake
from disnake.ext import commands
import wavelink

import yt_dlp
from core.misc.embed import custom_embed


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

    async def volume_change(self, interaction: disnake.MessageInteraction) -> None:
        player: wavelink.Player = interaction.guild.voice_client

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

        if new_volume > 100 or new_volume < 1:
            error_embed = custom_embed(color=disnake.Color.red())
            error_embed.title = f"Please enter a number, between `1` and `100`"
            return await response_modal.response.send_message(
                embed=error_embed, ephemeral=True
            )

        await player.set_volume(new_volume)
        await response_modal.response.send_message(
            embed=custom_embed(title=f"Set volume to {new_volume}"),
            ephemeral=True,
        )

    async def download_track(self, interaction: disnake.MessageInteraction) -> None:
        player: wavelink.Player = interaction.guild.voice_client

        if not player.current:
            embed = custom_embed(
                title="There are no songs in the queue yet",
                color=disnake.Color.red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        track: wavelink.Track = player.current

        await interaction.response.defer(ephemeral=True)
        file_like_object = io.BytesIO()

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{track.title}.mp3",
            "postprocessors": [],
        }

        async def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(track.uri, download=True)
                filename = ydl.prepare_filename(info)
                with open(filename, "rb") as f:
                    file_like_object.write(f.read())
                file_like_object.seek(0)  # Reset file pointer to the beginning

        # Run the download in an executor to avoid blocking the bot
        await download()

        # Send the file to the Discord channel
        file_like_object.seek(0)  # Ensure we're at the start of the file-like object
        await interaction.followup.send(
            file=disnake.File(file_like_object, "audio.mp3")
        )

        # Clean up
        file_like_object.close()

    async def callback(self, interaction: disnake.Interaction) -> None:
        selected_option = self.values[0]
        player: wavelink.Player = interaction.guild.voice_client

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

                track: wavelink.Track = player.current
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

            case "download":
                await self.download_track(interaction)

            case "disconnect":
                await player.disconnect()

                embed = custom_embed(
                    title=f"Disconnected from voice channel",
                    color=disnake.Colour.red(),
                )
                await interaction.response.edit_message(embed=embed, view=None)
