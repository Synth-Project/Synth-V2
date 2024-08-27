from typing import List

import disnake
from disnake.ext import commands

import wavelink

from core.misc.embed import custom_embed, CreatePaginator


class NavigationDropdown(disnake.ui.Select):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(
            placeholder="Choose an option",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(
                    label="Volume",
                    value="volume",
                ),
                disnake.SelectOption(
                    label="Shuffle",
                    value="shuffle",
                ),
                disnake.SelectOption(
                    label="Disconnect",
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

    async def callback(self, interaction: disnake.Interaction) -> None:
        selected_option = self.values[0]
        player: wavelink.Player = interaction.guild.voice_client

        match selected_option:
            case "volume":
                await self.volume_change(interaction)
            case "shuffle":
                player.queue.shuffle()
                track: wavelink.Track = player.current

                embed = custom_embed(
                    title="Shuffled the queue",
                    description=f"Current song: **{track.title}**\nNext song: **{player.queue[0].title}**",
                    color=disnake.Colour.green(),
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

            case "disconnect":
                await player.disconnect()

                embed = custom_embed(
                    title=f"Disconnected from voice channel",
                    color=disnake.Colour.red(),
                )
                await interaction.response.edit_message(embed=embed, view=None)


class NavigationPanel(disnake.ui.View):
    def __init__(
        self, bot: commands.bot, message_id: int, *, timeout: float | None = None
    ) -> None:
        super().__init__(timeout=timeout)
        self.message_id = message_id
        self.bot = bot

        self.add_item(NavigationDropdown(bot=self.bot))

    @disnake.ui.button(label="<", style=disnake.ButtonStyle.green, row=0)
    async def previous(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = interaction.guild.voice_client

        if not player.queue:
            return await interaction.response.send_message(
                "Sorry, the music queue is empty!",
                ephemeral=True,
            )

        if not player.playing:
            return await interaction.response.send_message(
                "Sorry, no music is currently playing!",
                ephemeral=True,
            )

        if player.queue.history and len(player.queue.history) > 0:
            setattr(player, "last_track", player.queue.history[-2])
            return await player.stop()

        # try:
        #     if len(player.queue.history) > 0:
        #         prev_track = player.queue.history[
        #             -2
        #         ]  # Get the last song in the history
        #         await player.play(prev_track)
        #         message = await interaction.channel.fetch_message(self.message_id)
        #         await message.delete()
        #         return await interaction.response.defer()

        # except (
        #     wavelink.InvalidClientException,
        #     wavelink.InvalidNodeException,
        #     disnake.Forbidden,
        # ):
        #     return await interaction.send(
        #         "Sorry, there was an error while processing your request.",
        #         ephemeral=True,
        #     )

    @disnake.ui.button(label=">", style=disnake.ButtonStyle.green, row=0)
    async def skip(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:

        player: wavelink.Player = interaction.guild.voice_client

        if not player.queue:
            return await interaction.response.send_message(
                "Sorry, the music queue is empty!",
                ephemeral=True,
            )

        try:
            await player.stop()
            message = await interaction.channel.fetch_message(self.message_id)
            await message.delete()
            await interaction.response.defer()

        except (
            wavelink.InvalidClientException,
            wavelink.InvalidNodeException,
            disnake.Forbidden,
            disnake.NotFound,
        ):
            pass

    @disnake.ui.button(label="Pause/Resume", style=disnake.ButtonStyle.gray, row=0)
    async def resume_and_pause(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = interaction.guild.voice_client

        if player.paused:
            await player.pause(False)
            await interaction.response.edit_message(content=f"")
        else:
            await player.pause(True)
            await interaction.response.edit_message(content=f"")

    @disnake.ui.button(label="Queue", style=disnake.ButtonStyle.blurple, row=0)
    async def queue(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        player: wavelink.Player = interaction.guild.voice_client

        if not player.queue:
            embed = disnake.Embed(
                title="Music Queue", description="No music in the queue"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embeds = [
            disnake.Embed(
                title="Music Queue",
                description="\n".join(
                    f"`{index}.` **{music.author} - {music.title}**"
                    for index, music in enumerate(player.queue, start=1)[i : i + 10]
                ),
            )
            for i in range(0, len(player.queue), 10)
        ]

        paginator = CreatePaginator(embeds=embeds, author_id=interaction.author.id)
        await interaction.response.send_message(
            embed=embeds[0], view=paginator, ephemeral=True
        )
