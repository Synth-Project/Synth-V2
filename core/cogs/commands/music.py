from datetime import timedelta
from typing import cast

import disnake
import wavelink
from disnake.ext import commands

# from core.cogs.autocomplete import play_autocomplete

from core.database.repositories.music import MusicRepository
from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed
from core.misc.music.functions import MusicFunctions
from core.misc.music.views.shuffle import ShuffleView
from core.misc.paginator import CreatePaginator


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Music, self).__init__()
        self.bot = bot
        self.repository = MusicRepository()
        self.functions = MusicFunctions()

    @commands.slash_command()
    async def player(self, _) -> None:
        pass

    @player.sub_command(description="Search and play music from nearly any platform")
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        *,
        query: str,
        volume: int = commands.Param(default=75, max_length=3, min_length=1),
    ) -> None:
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if query.startswith("❌"):
            error_embed.title = query
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        player: wavelink.Player = (
            interaction.guild.voice_client
            or await interaction.author.voice.channel.connect(cls=wavelink.Player)
        )
        await interaction.me.edit(deafen=True)

        await interaction.send(
            "<a:loading:1281259173639884882> Searching for tracks...",
            ephemeral=True,
        )

        if any(tag in query.lower() for tag in ["history:", "found:"]):
            tag, query = query.split(" ", maxsplit=1)

            if tag.lower().startswith("history:"):
                query = (
                    await MusicRepository().find_song(
                        author_id=interaction.author.id, query=query
                    )
                ).url

        tracks: wavelink.Search = await wavelink.Playable.search(
            query, source="spsearch"
        )

        if not tracks:
            error_embed.title = "❌ | Could not find any tracks with that query"
            await interaction.edit_original_response(content=None, embed=error_embed)
            return None

        if isinstance(tracks, wavelink.Playlist):
            for track in tracks.tracks:
                track.extras = {"requested_by": interaction.author.id}

            added: int = await player.queue.put_wait(tracks)
            track_info = {"track": f"{tracks.name} — {added} songs", "url": query}

            embed = CustomEmbed(
                title=f"Added playlist **{tracks.name}** ({added} songs) to the queue",
                author=interaction.author,
                footer_text=f"Volume: {player.volume}% // Synth Music 2024",
            ).get_embed()

            track: wavelink.Playable = (
                tracks[0] if not player.current else player.current
            )

        else:
            track: wavelink.Playable = tracks[0]
            track.extras = {"requested_by": interaction.author.id}

            await player.queue.put_wait(track)

            track_info = {
                "track": f"{track.title} — {track.author}",
                "url": track.uri,
                "source": track.source,
            }

            embed = CustomEmbed(
                title=f"Added track **{track.title}** to the queue",
                author=interaction.author,
                color=BasicColors.SUCCESS,
                footer_text=f"Volume: {player.volume}% // Synth Music 2024",
            ).get_embed()

        await self.repository.save_song(interaction.author.id, track_info)
        await self.functions.play_track(
            self.bot, interaction, player, embed, track, volume
        )

    @player.sub_command(name="skip", description="Skip the current track")
    async def skip(
        self, interaction: disnake.ApplicationCommandInteraction, track: str = None
    ):
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        queue = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )

        if not player:
            error_embed.title = "❌ | No active player found"
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        if track:
            for index, song in enumerate(queue):
                if track.lower() in f"{song.author} - {song.title}".lower():
                    track = player.queue[index]
                    player.queue.put_at(0, track)
                    break
            else:
                error_embed.title = (
                    "❌ | The specified track was not found in the queue!"
                )
                await interaction.send(embed=error_embed, ephemeral=True)
                return

        await self.functions.skip_track(player, interaction)

    @player.sub_command(name="previous", description="Skip to the previous track")
    async def previous(
        self, interaction: disnake.ApplicationCommandInteraction, track: str = None
    ):
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        queue = (
            player.queue
            if not player.queue.is_empty
            else (
                player.auto_queue
                if player.autoplay == wavelink.AutoPlayMode.enabled
                else player.queue
            )
        )

        if not player:
            error_embed.title = "❌ | No active player found"
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        if track:
            for index, song in enumerate(queue.history):
                if track.lower() in f"{song.author} - {song.title}".lower():
                    track = queue.history[index]
                    queue.put_at(0, track)
                    queue.put_at(1, player.current)
                    break
            else:
                error_embed.title = (
                    "❌ | The specified track was not found in the queue!"
                )
                await interaction.send(embed=error_embed, ephemeral=True)
                return
        else:
            previous_track = queue.history.get()
            queue.put_at(0, previous_track)
            queue.put_at(1, player.current)

        await self.functions.skip_track(player, interaction, True)

    @player.sub_command(name="volume", description="Set a new volume")
    async def volume(
        self, interaction: disnake.ApplicationCommandInteraction, volume: int
    ):
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if not player:
            error_embed.title = "❌ | No active player found"
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        volume = min(100, max(1, volume))
        await self.functions.set_volume(player, volume)
        await interaction.delete_original_response()

    @player.sub_command(name="queue", description="See a list of songs in the queue")
    async def queue(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if not player:
            error_embed.title = "❌ | No active player found"
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        if not player.queue:
            error_embed.title = "❌ | The queue is empty"
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        queue_list = list(enumerate(player.queue, start=1))

        embeds = [
            CustomEmbed(
                title=f"{interaction.guild.name}'s Queue",
                description="\n".join(
                    [
                        f"`[ {str(timedelta(seconds=round(music.length / 1000)))} ]` {music.title} // "
                        f"**{(await self.bot.get_or_fetch_user(music.extras.requested_by)).name if music.extras.requested_by else 'Unknown'}**"
                        for _, music in queue_list[i : i + 10]
                        if music
                    ]
                ),
            ).get_embed()
            for i in range(0, len(queue_list), 10)
        ]

        paginator = CreatePaginator(embeds=embeds, author_id=interaction.author.id)
        await interaction.send(embed=embeds[0], view=paginator, ephemeral=True)

    @player.sub_command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        error_embed = CustomEmbed.error_embed(author=interaction.author).get_embed()

        if not player:
            error_embed.title = "❌ | No active player found"
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        if not hasattr(player, "previous_queue"):
            player.previous_queue = player.queue.copy()
        if not hasattr(player, "previous_auto_queue"):
            player.previous_auto_queue = player.auto_queue.copy()

        (player.auto_queue if player.queue.is_empty else player.queue).shuffle()
        next_song = (
            player.queue[0] if not player.queue.is_empty else player.auto_queue[0]
        )

        embed = CustomEmbed(
            title="<:shuffle:1279835431315308605> Shuffled the queue",
            description=f"Current song: **{player.current.title}**\nNext song: **{next_song.title}**",
            color=BasicColors.SUCCESS,
        ).get_embed()
        await interaction.send(
            embed=embed,
            ephemeral=True,
            view=ShuffleView(
                self.bot, interaction, player.previous_queue, player.previous_auto_queue
            ),
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
