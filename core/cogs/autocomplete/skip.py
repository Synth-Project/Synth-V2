import disnake
from disnake.ext import commands
import wavelink

from core.cogs.commands.music import Music
from core.misc.misc import shorten_text


class SkipAutocomplete(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(SkipAutocomplete, self).__init__()
        self.bot = bot

    @Music.skip.autocomplete("track")
    async def skip_autocomplete(
        interaction: disnake.ApplicationCommandInteraction, search_query: str
    ):
        player: wavelink.Player = (
            interaction.guild.voice_client
            or await interaction.author.voice.channel.connect(cls=wavelink.Player)
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

        if not interaction.author.voice:
            return await interaction.response.autocomplete(
                choices=["❌ | You are not in a voice channel"]
            )

        if not search_query:
            autocomplete_list = (
                [shorten_text(f"{song.author} - {song.title}") for song in queue_[:25]]
                if len(queue_) > 0
                else ["❌ | There are no songs in the queue"]
            )
            return await interaction.response.autocomplete(choices=autocomplete_list)

        matching_songs = [
            shorten_text(f"{song.author} - {song.title}")
            for song in queue_
            if search_query.lower() in song.title.lower()
        ]

        autocomplete_list = (
            matching_songs[:25]
            if matching_songs
            else ["❌ | No song with that name in the queue"]
        )

        await interaction.response.autocomplete(choices=autocomplete_list)


def setup(bot: commands.Bot):
    bot.add_cog(SkipAutocomplete(bot))
