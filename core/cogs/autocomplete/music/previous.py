import disnake
from disnake.ext import commands
import wavelink

from core.cogs.commands.music import Music
from core.misc.misc import shorten_text


class PreviousAutocomplete(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(PreviousAutocomplete, self).__init__()
        self.bot = bot

    @Music.previous.autocomplete("track")
    async def previous_autocomplete(
        self, interaction: disnake.ApplicationCommandInteraction, search_query: str
    ):
        if not interaction.author.voice:  # type: ignore
            return await interaction.response.autocomplete(
                choices=["❌ | You are not in a voice channel"]
            )

        player: wavelink.Player = (
            interaction.guild.voice_client  # type: ignore
            or await interaction.author.voice.channel.connect(cls=wavelink.Player)  # type: ignore
        )

        queue_ = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )

        history = queue_.history or []

        if not search_query:
            autocomplete_list: list = (
                [shorten_text(f"{song.author} - {song.title}") for song in history[:25]]
                if history
                else ["❌ | There are no songs has been played before"]
            )
        else:
            matching_songs = [
                shorten_text(f"{song.author} - {song.title}")
                for song in history
                if search_query.lower() in song.title.lower()
            ]
            autocomplete_list = (
                matching_songs[:25]
                if matching_songs
                else ["❌ | No song with that name in the queue"]
            )

        await interaction.response.autocomplete(choices=autocomplete_list)


def setup(bot: commands.Bot):
    bot.add_cog(PreviousAutocomplete(bot))
