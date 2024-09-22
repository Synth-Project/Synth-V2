import disnake

from core.misc.fun.chess import ChessGame


class ChessSurrenderView(disnake.ui.View):
    def __init__(
        self, game: ChessGame, interaction: disnake.ApplicationCommandInteraction
    ):
        super().__init__()
        self.game = game
        self.interaction = interaction

    @disnake.ui.button(label="Confirm Surrender", style=disnake.ButtonStyle.danger)
    async def confirm_button(
        self, _: disnake.ui.Button, interaction: disnake.ApplicationCommandInteraction
    ):
        if interaction.user.id != self.game.current_turn:
            return await interaction.response.send_message(
                "You cannot surrender for another player.", ephemeral=True
            )

        await self.game.handle_game_end(
            interaction, f"<@{interaction.user.id}> surrendered!"
        )
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.secondary)
    async def cancel_button(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_message("Surrender cancelled.", ephemeral=True)
        self.stop()
