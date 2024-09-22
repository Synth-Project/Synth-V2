import disnake

from core.misc.fun.chess import ChessGame


class ChessChallengeView(disnake.ui.View):
    def __init__(
        self,
        player1: int,
        player2: int,
        cog,
        interaction: disnake.Interaction,
    ):
        super().__init__(timeout=30.0)
        self.players = (player1, player2)
        self.interaction = interaction
        self.cog = cog

    @disnake.ui.button(label="Accept", style=disnake.ButtonStyle.green)
    async def accept_button(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer()

        game = ChessGame(*self.players, self.cog.engine)
        self.cog.games[tuple(self.players)] = game
        await game.send_board(interaction)

        if self.players[0] == self.cog.bot.user.id:
            await game.bot_move()

        await interaction.send(
            f"Game started between <@{self.players[0]}> and <@{self.players[1]}>!",
        )
        await self.interaction.delete_original_response()
        self.stop()

    @disnake.ui.button(label="Decline", style=disnake.ButtonStyle.red)
    async def decline_button(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.send(f"<@{self.players[1]}> declined the game.")
        await self.interaction.delete_original_response()
        self.stop()

    async def on_timeout(self) -> None:
        await self.interaction.edit_original_response("Timed out.", view=None)
        self.stop()

    async def interaction_check(self, interaction: disnake.Interaction) -> bool:
        if (
            interaction.author.id in list(self.players)
            and interaction.author.id == self.interaction.author.id
        ):
            await interaction.send(
                "You don't have permission to use this button", ephemeral=True
            )
            return False
        return True
