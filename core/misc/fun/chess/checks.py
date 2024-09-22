import chess
import disnake


class ChessChecks:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_game_key(games: dict, player_id: int):
        """Finds the game key where the player is involved."""
        return next((key for key in games if player_id in key), None)

    @staticmethod
    async def check_active_game(
        interaction: disnake.ApplicationCommandInteraction, games: dict
    ):
        """Checks if the player has an active game and returns the game key."""
        game_key = ChessChecks.get_game_key(games, interaction.author.id)
        if not game_key:
            await interaction.response.send_message(
                "You have no active game.", ephemeral=True
            )
        return game_key

    @staticmethod
    async def validate_turn(interaction: disnake.ApplicationCommandInteraction, game):
        """Validates if it's the player's turn."""
        if interaction.author.id != game.current_turn:
            await interaction.response.send_message(
                "It's not your turn.", ephemeral=True
            )
            return False
        return True

    @staticmethod
    async def validate_move(
        interaction: disnake.ApplicationCommandInteraction,
        game,
        from_square: str,
        to_square: str,
    ):
        """Validates the move and returns a list of possible legal moves."""
        move = chess.Move.from_uci(from_square + to_square)

        if move not in game.legal_moves:
            possible_moves = [
                m.uci()
                for m in game.legal_moves
                if from_square in chess.SQUARE_NAMES[m.from_square]
                or to_square in chess.SQUARE_NAMES[m.to_square]
            ]
            moves_list = (
                ", ".join(f"{move[:2]} {move[2:]}" for move in possible_moves)
                if possible_moves
                else "No possible moves."
            )
            await interaction.response.send_message(
                f"Invalid move. Possible moves: {moves_list}", ephemeral=True
            )
            return False
        return move
