import disnake

from typing import Optional, Union
from core.database.models.guild import GuildModel
from core.database.models.music import UserMusic as Music
from core.database.repositories.base import BaseRepository


class GuildMusicRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    async def get_one(**kwargs) -> GuildModel | None:
        return await GuildModel.filter(**kwargs).first()

    @staticmethod
    async def get_all(**kwargs) -> list[GuildModel]:
        return await GuildModel.filter(**kwargs).all()

    async def add_one(self, **kwargs) -> tuple[GuildModel, bool]:
        model, is_created = await GuildModel.get_or_create(**kwargs)
        # if is_created:
        #     await model.fetch_related("music_settings")
        return model, is_created

    async def remove_one(self, **kwargs) -> None:
        await GuildModel.filter(**kwargs).delete()

    async def find_dj_role(self, guild_id: int) -> Optional[str]:
        guild = await self.get_one(id=guild_id)

        if not guild or not guild.music_settings:
            return

        return guild.music_settings.get("dj_role")
        # return await GuildModel.filter(guild_id=guild_id).first()

    async def set_dj_role(
        self, guild_id: int, role_id: Union[int, disnake.Role]
    ) -> GuildModel | None:
        if isinstance(role_id, disnake.Role):
            role_id = role_id.id

        guild, created = await self.add_one(id=guild_id)

        print(guild)

        if not guild and not created:
            return

        guild.music_settings.update({"dj_role": role_id})
        await guild.save()
        return guild
        # return await guild.music_settings(dj_role=role_id)

    # async def find_song(self, author_id: int, query: str) -> Music | None:
    #     user = await self.get_one(id=author_id)

    #     if not user or not await user.musics.filter(name=query).exists():
    #         return

    #     return await Music.filter(name=query).first()

    # async def save_song(self, author_id: int, track: dict[str, str]):
    #     user_model, _ = await self.add_one(id=author_id)
    #     await user_model.fetch_related("musics")

    #     if not await user_model.musics.filter(url=track["url"]).exists():
    #         if len(user_model.musics) >= 3:
    #             await user_model.musics.remove(user_model.musics[0])
    #         await user_model.musics.add(
    #             await Music.create(name=track["track"], url=track["url"])
    #         )

    #     result = await self.get_one(id=author_id)
    #     return await result.musics.filter(url=track["url"]).first()
