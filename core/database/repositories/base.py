from abc import ABC, abstractmethod
from typing import Any


class BaseRepository(ABC):
    ModelType = Any

    @abstractmethod
    async def get_one(self, **kwargs) -> ModelType:
        pass

    @abstractmethod
    async def get_all(self, **kwargs) -> list[ModelType]:
        pass

    @abstractmethod
    async def add_one(self, **kwargs) -> tuple[ModelType, bool]:
        pass

    @abstractmethod
    async def remove_one(self, **kwargs) -> None:
        pass
