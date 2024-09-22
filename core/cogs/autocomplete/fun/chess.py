from typing import Union

import chess
import disnake
from disnake.ext import commands

from core.cogs.commands.chess import ChessCog


class ChessAutocomplete(commands.Cog):
    def __init__(self, bot: commands.Bot, games: dict) -> None:
        self.bot = bot
        self.games = games

    @ChessCog.chess_move.autocomplete("from_square")
    async def autocomplete_from_square(
        self, interaction: disnake.ApplicationCommandInteraction, query: str
    ):
        """Generates the autocomplete list for the 'from_square'."""
        chess_cog: Union[ChessCog, commands.Cog] = self.bot.get_cog("ChessCog")
        game = chess_cog.games.get_game_for_player(interaction.author.id)

        if not game:
            return ["❌ | No active game found."]

        valid_moves = set(move.from_square for move in game.legal_moves)
        valid_squares = [chess.square_name(square) for square in valid_moves]
        print(valid_squares, valid_moves)
        return await interaction.response.autocomplete(
            choices=[square for square in valid_squares if square.startswith(query)]
        )

    @ChessCog.chess_move.autocomplete("to_square")
    async def autocomplete_to_square(
        self, interaction: disnake.ApplicationCommandInteraction, query: str
    ):
        """Generates the autocomplete list for the 'to_square' based on the 'from_square'."""
        chess_cog: Union[ChessCog, commands.Cog] = self.bot.get_cog("ChessCog")
        game = chess_cog.games.get_game_for_player(interaction.author.id)

        if not game:
            return ["❌ | No active game found."]

        from_square = interaction.filled_options.get("from_square")

        if not from_square:
            return ["❌ | No from_square provided."]

        from_square = chess.parse_square(from_square)
        valid_moves = [
            move for move in game.legal_moves if move.from_square == from_square
        ]
        valid_squares = [chess.square_name(move.to_square) for move in valid_moves]
        print(valid_squares, valid_moves)
        return await interaction.response.autocomplete(
            choices=[square for square in valid_squares if square.startswith(query)]
        )


def setup(bot: commands.Bot, games: dict) -> None:
    bot.add_cog(ChessAutocomplete(bot, games))
