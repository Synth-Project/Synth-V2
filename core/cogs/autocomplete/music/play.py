import disnake
from disnake.ext import commands
import wavelink

from core.cogs.commands.music import Music
from core.database.repositories.music import MusicRepository
from core.misc.misc import shorten_text
import re

patterns = {
    "spsearch": r"https?://open\.spotify\.com/(track|playlist|show|episode|album)/[A-Za-z0-9]+",
    "ytmsearch": r"https?://music\.youtube\.com/(watch\?v=[\w-]+|playlist\?list=[\w-]+|track\?id=[\w-]+)",
    "ytsearch": r"https?://(www\.)?youtube\.com/(watch\?v=[\w-]+|playlist\?list=[\w-]+)",
    "dzsearch": r"https?://(www\.)?deezer\.com(/[a-z]{2})?/(track|playlist|album)/[\w-]+|https?://deezer\.page\.link/[A-Za-z0-9]+",
    "scsearch": r"https?://soundcloud\.com/[A-Za-z0-9-]+/(sets/)?[A-Za-z0-9-]+",
    "amsearch": r"https?://music\.apple\.com/[a-z]{2}/(album|playlist)/[A-Za-z0-9-]+",
}


class PlayAutocomplete(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(PlayAutocomplete, self).__init__()
        self.bot = bot

    @Music.play.autocomplete("query")
    async def play_autocomplete(
        self, interaction: disnake.ApplicationCommandInteraction, search_query: str
    ):
        if not interaction.author.voice:
            return await interaction.response.autocomplete(
                choices=["❌ | You are not in a voice channel"]
            )

        if not search_query:
            result, _ = await MusicRepository().add_one(id=interaction.author.id)
            autocomplete_list = (
                [
                    f"History: {shorten_text(song.name)}"
                    for song in await result.songs.all()
                ]
                if result and await result.songs.all().count() > 0
                else ["❌ | Try to add a song for the first time"]
            )
            return await interaction.response.autocomplete(choices=autocomplete_list)

        source = next(
            (
                source
                for source, pattern in patterns.items()
                if re.match(pattern, search_query)
            ),
            "spsearch",
        )
        try:
            search_results = await wavelink.Playable.search(search_query, source=source)
            autocomplete_options = [
                (
                    f"Found: {shorten_text(f'{track.title} — {track.author}')} | {track.source}"
                    if source == "spsearch"
                    else f"Found: {shorten_text(f'{track.title} — {track.author}')}"
                )
                for index, track in enumerate(search_results)
                if index < 25
            ]
            if not autocomplete_options:
                autocomplete_options = [
                    "❌ | Could not find any tracks with that query"
                ]
            return await interaction.response.autocomplete(choices=autocomplete_options)
        except Exception as e:
            print(f"Error fetching track: {e}")
            return await interaction.response.autocomplete(
                choices=["❌ | Something went wrong with your request"]
            )


def setup(bot: commands.Bot):
    bot.add_cog(PlayAutocomplete(bot))
