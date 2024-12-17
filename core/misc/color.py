from disnake import Guild

from enum import Enum, IntEnum


class BasicColors(IntEnum):
    DEFAULT: int = 0x2F3236
    WARNING: int = 0xF5E042
    ERROR: int = 0xF54242
    SUCCESS: int = 0x4EF542


class CustomColors:
    def __init__(self, guild: Guild):
        self.guild = guild

    def get_default_color(self) -> int:
        # should be moved to another branch with this implementation
        pass
