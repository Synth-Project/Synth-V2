import disnake
from wavelink import Player


class CustomPlayer(Player):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.message: disnake.Message = None
