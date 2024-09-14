from core.database.models import UserModel, BirthdayModel
from core.database.repositories.base import BaseRepository


class BirthdayRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    # async def __aenter__(self: Self) -> Self:
    #     return self

    # async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
    #     return None

    @staticmethod
    async def get_one(**kwargs) -> UserModel | None:
        return await UserModel.filter(**kwargs).first().prefetch_related("birthday")

    @staticmethod
    async def get_all(**kwargs) -> list[UserModel]:
        return await UserModel.filter(**kwargs).all().prefetch_related("birthday")

    @staticmethod
    async def add_one(**kwargs) -> tuple[UserModel, bool]:
        return await UserModel.get_or_create(**kwargs)

    @staticmethod
    async def remove_one(**kwargs):
        return await UserModel.filter(**kwargs).delete()

    async def save_birthday(self, author_id: int, day: int, month: int):
        result = await self.get_one(id=author_id)
        birthday = await BirthdayModel.create(day=day, month=month)

        if not result:
            await UserModel.create(id=author_id, birthday=birthday)
        else:
            await result.create(birthday=birthday)

        result = await self.get_one(id=author_id)

        return result
