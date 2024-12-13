from enum import Enum


class Emojis(Enum):
    TEST = "test"

    def __str__(self) -> str:
        return self.value

    __repr__ = __str__
