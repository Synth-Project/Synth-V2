from core.database.models.user import UserModel
from core.database.models.music import Song
from core.database.repositories.base import BaseRepository


class MusicRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    async def get_one(**kwargs) -> UserModel | None:
        return await UserModel.filter(**kwargs).first().prefetch_related("songs")

    @staticmethod
    async def get_all(**kwargs) -> list[UserModel]:
        return await UserModel.filter(**kwargs).all().prefetch_related("songs")

    @staticmethod
    async def add_one(**kwargs) -> tuple[UserModel, bool]:
        model, is_created = await UserModel.get_or_create(**kwargs)
        if is_created:
            await model.fetch_related("songs")
        return model, is_created

    @staticmethod
    async def remove_one(**kwargs):
        return await UserModel.filter(**kwargs).delete()

    async def find_song(self, author_id: int, query: str) -> Song | None:
        user = await self.get_one(id=author_id)

        if not user or not await user.songs.filter(name=query).exists():
            return

        return await Song.filter(name=query).first()

    async def save_song(self, author_id: int, track: dict[str, str]):
        user_model, _ = await self.add_one(id=author_id)
        await user_model.fetch_related("songs")

        if not await user_model.songs.filter(url=track["url"]).exists():
            if len(user_model.songs) >= 3:
                await user_model.songs.remove(user_model.songs[0])
            await user_model.songs.add(
                await Song.create(name=track["track"], url=track["url"])
            )

        result = await self.get_one(id=author_id)
        return await result.songs.filter(url=track["url"]).first()
