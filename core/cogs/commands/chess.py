import random

import chess
import chess.engine
import chess.svg
import disnake
from disnake.ext import commands

from core.bot import Bot
from core.misc.fun.chess import ChessGame, ChessChecks
from core.misc.fun.chess.views import ChessChallengeView, ChessSurrenderView


class ChessCog(commands.Cog):
    def __init__(self, bot: "Bot") -> None:
        self.bot = bot
        self.games = ChessGame(self.bot, None, None, None)

    @commands.slash_command()
    async def chess(self, _: disnake.ApplicationCommandInteraction):
        pass

    @chess.sub_command(name="new", description="Start a new chess game")
    async def chess_new(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        player1 = interaction.author.id
        player2 = member.id if member else self.bot.user.id

        if player1 == player2:
            return await interaction.response.send_message(
                "You cannot play against yourself!", ephemeral=True
            )

        game = self.games.get_game_for_player(player1)
        if game:
            player = (
                "the bot"
                if game.players[0] == self.bot.user.id
                or game.players[1] == self.bot.user.id
                else f"<@{game.players[0] if game.players[0] != player1 else game.players[1]}>"
            )
            return await interaction.response.send_message(
                f"You are already playing with {player}. "
                f"[Go to the game]({game.message.jump_url})",
                ephemeral=True,
            )

        if member:
            view = ChessChallengeView(player1, player2, self, interaction)
            await interaction.send(
                f"<@{player2}>, <@{player1}> wants to play chess. Will you accept the challenge?",
                view=view,
            )
        else:
            transport, engine = await chess.engine.popen_uci("/usr/bin/stockfish")
            game = (
                ChessGame(self.bot, player1, player2, engine)
                if random.choice([True, False])
                else ChessGame(self.bot, player2, player1, engine)
            )

            self.games.add_game((player1, player2), game)
            await game.send_board(interaction)

            if game.current_turn == self.bot.user.id:
                await game.bot_move()

    @chess.sub_command(name="move", description="Move a piece on the board")
    async def chess_move(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        from_square: str,
        to_square: str,
    ):
        game = self.games.get_game_for_player(interaction.author.id)
        if not game or not await ChessChecks.validate_turn(interaction, game):
            return

        if not (
            move := await ChessChecks.validate_move(
                interaction, game, from_square, to_square
            )
        ):
            return

        game.make_move(move)
        await game.update_board_message(move)

        await interaction.send(f"Moved {from_square} to {to_square}", ephemeral=True)

        if game.is_game_over:
            return await game.handle_game_end(
                interaction, f"<@{game.current_turn}> won!"
            )

        if game.current_turn == self.bot.user.id:
            await game.bot_move()

    @chess.sub_command(name="surrender", description="Surrender the current game")
    async def chess_surrender(self, interaction: disnake.ApplicationCommandInteraction):
        game = self.games.get_game_for_player(interaction.author.id)

        if not game:
            return await interaction.response.send_message(
                "You are not in an active game.", ephemeral=True
            )

        if game.current_turn != interaction.author.id:
            return await interaction.response.send_message(
                "It's not your turn to surrender.", ephemeral=True
            )

        view = ChessSurrenderView(game, interaction)
        await interaction.response.send_message(
            f"Are you sure you want to surrender?", view=view, ephemeral=True
        )


def setup(bot: commands.Bot):
    from core.cogs.autocomplete.fun.chess import ChessAutocomplete

    bot.add_cog(ChessCog(bot))
    if bot.get_cog("ChessAutocomplete") is None:
        bot.add_cog(ChessAutocomplete(bot, bot.get_cog("ChessCog").games))
