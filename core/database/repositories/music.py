from core.database.models.music import MusicModel, Song
from core.database.repositories.base import BaseRepository


class MusicRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    # async def __aenter__(self: Self) -> Self:
    #     return self

    # async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
    #     return None

    @staticmethod
    async def get_one(**kwargs) -> MusicModel | None:
        return await MusicModel.filter(**kwargs).first().prefetch_related("songs")

    @staticmethod
    async def get_all(**kwargs) -> list[MusicModel]:
        return await MusicModel.filter(**kwargs).all().prefetch_related("songs")

    @staticmethod
    async def add_one(**kwargs) -> tuple[MusicModel, bool]:
        return await MusicModel.get_or_create(**kwargs)

    @staticmethod
    async def remove_one(**kwargs):
        return await MusicModel.filter(**kwargs).delete()

    async def find_song(self, author_id: int, query: str) -> Song | None:
        user_track = await self.get_one(user_id=author_id)

        if not user_track or not await user_track.songs.filter(name=query).exists():
            return

        return await Song.filter(name=query).first()

    # async def save_song(self, author_id: int, track: dict[str, str]):
    #     result = await self.get_one(user_id=author_id)
    #
    #     if not result:
    #         music_model = await MusicModel.create(user_id=author_id)
    #         song = await Song.create(name=track["track"], url=track["url"])
    #         await music_model.songs.add(song)
    #
    #     else:
    #         if not await result.songs.filter(url=track["url"]).exists():
    #             if len(result.songs) >= 3:
    #                 await result.songs.remove(result.songs[0])
    #
    #             await result.songs.add(
    #                 await Song.create(name=track["track"], url=track["url"])
    #             )
    #
    #     result = await self.get_one(user_id=author_id)
    #     return result.songs.filter(url=track["url"]).first()

    async def save_song(self, author_id: int, track: dict[str, str]):
        music_model, _ = await self.add_one(user_id=author_id)
        await music_model.fetch_related("songs")

        if not await music_model.songs.filter(url=track["url"]).exists():
            if len(music_model.songs) >= 3:
                await music_model.songs.remove(music_model.songs[0])
            await music_model.songs.add(await Song.create(name=track["track"], url=track["url"]))

        result = await self.get_one(user_id=author_id)
        return await result.songs.filter(url=track["url"]).first()
