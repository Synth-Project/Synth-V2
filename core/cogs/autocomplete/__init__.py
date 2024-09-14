import disnake
import wavelink

from core.database.repositories.music import MusicRepository
from core.misc.misc import shorten_text


async def play_autocomplete(
    interaction: disnake.ApplicationCommandInteraction, search_query: str
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
                for song in (await result.songs.all())
            ]
            if result and await result.songs.all().count() > 0
            else ["❌ | Try to add a song for the first time"]
        )

        return await interaction.response.autocomplete(choices=autocomplete_list)

    search_results = await wavelink.Playable.search(search_query, source="spsearch")
    autocomplete_options = [
        f"Found: {shorten_text(f'{track.title} — {track.author}')}"
        for index, track in enumerate(search_results)
        if index < 25
    ]

    if not autocomplete_options:
        autocomplete_options = ["❌ | Could not find any tracks with that query"]

    await interaction.response.autocomplete(choices=autocomplete_options)


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
