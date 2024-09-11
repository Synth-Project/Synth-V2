from core.database.models import UserModel, Remind
from core.database.models.reminder import ReminderType
from core.database.repositories.base import BaseRepository


class ReminderRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    # async def __aenter__(self: Self) -> Self:
    #     return self

    # async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
    #     return None

    @staticmethod
    async def get_one(**kwargs) -> UserModel | None:
        return await UserModel.filter(**kwargs).first().prefetch_related("reminds")

    @staticmethod
    async def get_all(**kwargs) -> list[UserModel]:
        return await UserModel.filter(**kwargs).all().prefetch_related("reminds")

    @staticmethod
    async def get_all_reminds(**kwargs) -> list[Remind]:
        return await Remind.filter(**kwargs).all()

    @staticmethod
    async def add_one(**kwargs) -> tuple[UserModel, bool]:
        return await UserModel.get_or_create(**kwargs)

    @staticmethod
    async def remove_one(**kwargs):
        return await UserModel.filter(**kwargs).delete()

    async def find_remind(
        self, author_id: int, time: int, type: ReminderType
    ) -> Remind | None:
        user_model = await self.get_one(id=author_id)

        if (
            not user_model
            or not await user_model.reminds.filter(time=time, type=type).exists()
        ):
            return

        return await Remind.filter(time=time, type=type).first()

    async def save_remind(
        self, author_id: int, text: str, time: int, channel_id: int, type: ReminderType
    ):
        result = await self.get_one(id=author_id)

        if not result:
            user_model = await UserModel.create(id=author_id)
            remind = await Remind.create(
                text=text, time=time, channel_id=channel_id, type=type
            )
            await user_model.reminds.add(remind)
        else:
            await result.reminds.add(
                await Remind.create(
                    text=text, time=time, channel_id=channel_id, type=type
                )
            )

        result = await self.get_one(id=author_id)

        return result.reminds.filter(time=time, type=type).first()
