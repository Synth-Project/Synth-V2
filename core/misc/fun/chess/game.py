import io
from typing import Optional

import chess
import chess.engine
import chess.svg
import disnake
from cairosvg import svg2png
from chess.engine import UciProtocol
from disnake.ext import commands

from core.misc.color import BasicColors
from core.misc.embed import CustomEmbed


class ChessGame:
    def __init__(
        self,
        bot: commands.Bot,
        player1: Optional[int],
        player2: Optional[int],
        engine: Optional[UciProtocol],
    ):
        self.bot = bot
        self.board = chess.Board()
        self.players = (player1, player2)
        self.current_turn = player1
        self.engine: UciProtocol = engine
        self.message: Optional[disnake.Message] = None

        self._games: dict[tuple[int, int], "ChessGame"] = {}
        self.move_history: list[chess.Move] = []

    @property
    def games(self):
        return self._games

    @staticmethod
    def get_game_key(games: dict, player_id: int):
        return next((key for key in games if player_id in key), None)

    def is_player_in_game(self, player_id: int) -> bool:
        return self.get_game_key(self.games, player_id) is not None

    def get_game_for_player(self, player_id: int) -> Optional["ChessGame"]:
        game_key = self.get_game_key(self.games, player_id)
        return self.games.get(game_key) if game_key else None

    @property
    def is_game_over(self):
        return self.board.is_game_over()

    @property
    def legal_moves(self):
        return self.board.legal_moves

    @property
    def is_checkmate(self):
        return self.board.is_checkmate()

    @property
    def is_stalemate(self):
        return self.board.is_stalemate()

    @property
    def is_draw(self):
        return (
            self.board.is_insufficient_material()
            or self.board.is_seventyfive_moves()
            or self.board.is_fivefold_repetition()
        )

    async def handle_game_end(
        self, _: disnake.ApplicationCommandInteraction, result: str
    ):
        """Handle the end of the game, sending a message with the result."""
        await self.message.reply(f"Game over. {result}")
        await self.analyze_game()
        self.games.pop((self.players[0], self.players[1]), None)

    def add_game(self, key: tuple[int, int], game: "ChessGame"):
        self.games[key] = game

    def get_game(self, key: tuple[int, int]) -> "ChessGame":
        return self.games.get(key)

    def remove_game(self, key: tuple[int, int]):
        if key in self.games:
            del self.games[key]

    def make_move(self, move):
        self.board.push(move)
        self.move_history.append(move)
        self.current_turn = (
            self.players[1] if self.current_turn == self.players[0] else self.players[0]
        )

    def get_board(self, last_move=None) -> bytes:
        board = chess.svg.board(board=self.board, lastmove=last_move)
        return svg2png(bytestring=board.encode("utf-8"))

    async def bot_move(self):
        async with self.message.channel.typing():
            result = await self.engine.play(self.board, chess.engine.Limit(time=5.0))
            self.make_move(result.move)
            await self.update_board_message(result.move)

    async def update_board_message(self, last_move=None):
        image = self.get_board(last_move)
        embed = CustomEmbed(title="Chess", color=BasicColors.SUCCESS).get_embed()
        embed.set_image(url="attachment://board.png")
        await self.message.edit(
            attachments=[],
            files=[disnake.File(io.BytesIO(image), filename="board.png")],
        )
        await self.message.reply(
            content=f"Now it's <@{self.current_turn}>'s turn!", delete_after=3
        )

    async def send_board(self, inter: disnake.Interaction) -> disnake.Message:
        image = self.get_board()
        self.message = await inter.channel.send(
            file=disnake.File(io.BytesIO(image), filename="board.png")
        )

        return self.message

    async def analyze_game(self) -> None:
        analysis_results = []

        player1, player2 = self.players
        board = chess.Board()

        move_types = {
            (600, float("inf")): "Brilliant",
            (300, 600): "Excellent",
            (100, 300): "Good",
            (-100, 100): "Normal",
            (-300, -100): "Mistake",
            (-float("inf"), -300): "Blunder",
        }

        for i, move in enumerate(self.move_history):
            board.push(move)
            info = await self.engine.analyse(board, chess.engine.Limit(time=0.2))

            player = ("WHITE", player1) if i % 2 == 0 else ("BLACK", player2)

            if player[1] == self.bot.user.id:
                continue

            score = (
                info["score"].white().score(mate_score=1000)
                if i % 2 == 0
                else info["score"].black().score(mate_score=1000)
            )

            move_type = next(
                type_
                for (low, high), type_ in move_types.items()
                if low <= score < high
            )
            analysis_results.append(
                f"**{player[0]} (<@{player[1]}>)**:\n -> **Move**: from {move.uci()[:2]} to {move.uci()[2:]}\n -> **Score:** {score}\n -> **Type:** {move_type}\n"
            )

        summary = "\n".join(analysis_results)

        await self.message.reply(
            embed=CustomEmbed(title="Chess | Analysis", description=summary).get_embed()
        )
        return
