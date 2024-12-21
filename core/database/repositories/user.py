import disnake
from typing import Optional
from datetime import datetime

from tortoise.transactions import atomic

from core.database.repositories.base import BaseRepository
from core.database.models.user import UserModel
from core.database.models.warns import WarnsModel


class UserRepository(BaseRepository):
    ModelType = UserModel

    async def get_one(self, **kwargs) -> Optional[UserModel]:
        return await UserModel.filter(**kwargs).first().prefetch_related("warns")

    async def get_all(self, **kwargs) -> list[UserModel]:
        return await UserModel.filter(**kwargs).all().prefetch_related("warns")

    async def add_one(self, **kwargs) -> tuple[UserModel, bool]:
        model, created = await UserModel.get_or_create(**kwargs)
        return model, created

    async def remove_one(self, **kwargs) -> None:
        await UserModel.filter(**kwargs).delete()

    # @atomic()
    async def add_warn(
        self,
        user_id: int,
        warned_by: int,
        reason: Optional[str] = None,
        remove_at: Optional[datetime] = None,
    ) -> WarnsModel:
        """
        Add a warn to a specific user.

        :param user_id: ID of the user to warn
        :param reason: Optional reason for the warn
        :param warned_by: ID of the moderator who issued the warn
        :param remove_at: Optional datetime when the warn should be removed
        :return: Created WarnsModel instance
        """
        user, _ = await UserModel.get_or_create(id=user_id)

        last_warn = await WarnsModel.filter(user=user).order_by("-warn_id").first()
        next_warn_id = last_warn.warn_id + 1 if last_warn else 1

        warn = WarnsModel(
            user=user,
            reason=reason,
            warn_id=next_warn_id,
            warned_by=warned_by,
            remove_at=remove_at,
        )
        await warn.save()

        return warn

    async def get_warn(self, user_id: int, warn_id: int) -> Optional[WarnsModel]:
        user = await UserModel.get_or_none(id=user_id)
        if not user:
            return None

        return await WarnsModel.filter(user=user, warn_id=warn_id).first()

    async def get_warns(self, user_id: int) -> list[WarnsModel]:
        """
        Retrieve all warns for a specific user.

        :param user_id: ID of the user to retrieve warns for
        :return: List of WarnsModel instances
        """
        user = await UserModel.get_or_none(id=user_id)
        if not user:
            return []

        return await WarnsModel.filter(user=user).order_by("warn_id").all()

    async def get_all_warns(self) -> list[WarnsModel]:
        return await WarnsModel.all().order_by("id").prefetch_related("user")

    async def remove_warn(self, user_id: int, warn_id: int) -> bool:
        """
        Remove a specific warn from a user.

        :param user_id: ID of the user
        :param warn_id: ID of the warn to remove
        :return: True if warn was removed, False otherwise
        """
        user = await UserModel.get_or_none(id=user_id)
        if not user:
            return False

        warn = await WarnsModel.get_or_none(user=user, warn_id=warn_id)
        if not warn:
            return False

        await warn.delete()
        return True

    async def clear_warns(self, user_id: int) -> int:
        """
        Clear all warns for a specific user.

        :param user_id: ID of the user
        :return: Number of warns deleted
        """
        user = await UserModel.get_or_none(id=user_id)
        if not user:
            return 0

        return await WarnsModel.filter(user=user).delete()
