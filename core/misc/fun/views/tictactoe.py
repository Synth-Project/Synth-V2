import disnake

from core.misc.embed import CustomEmbed


class ConfirmView(disnake.ui.View):
    def __init__(self, confirmer: disnake.Member):
        super().__init__(timeout=180)
        self.confirmer = confirmer
        self.value = None

    @disnake.ui.button(label="Yes", style=disnake.ButtonStyle.success)
    async def confirm(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        if interaction.user != self.confirmer:
            embed = CustomEmbed.error_embed(
                author=interaction.user,
                title="❌ | You are not the confirmer!",
            ).get_embed()
            await interaction.send(embed=embed, ephemeral=True)
            return
        self.value = True
        self.stop()

    @disnake.ui.button(label="No", style=disnake.ButtonStyle.danger)
    async def cancel(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        if interaction.user != self.confirmer:
            embed = CustomEmbed.error_embed(
                author=interaction.user,
                title="❌ | You are not the confirmer!",
            ).get_embed()
            await interaction.send(embed=embed, ephemeral=True)
            return

        self.value = False
        self.stop()


class TicTacToeView(disnake.ui.View):
    def __init__(self, player1: disnake.Member, player2: disnake.Member):
        super().__init__(timeout=None)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [""] * 9

        for i in range(9):
            self.add_item(TicTacToeButton(i))

    def check_win(self) -> bool:
        """Checks if there's a winner."""
        win_conditions = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]
        for cond in win_conditions:
            a, b, c = cond
            if self.board[a] == self.board[b] == self.board[c] and self.board[a] != "":
                self.winner = self.current_player
                return True
        return False

    def check_draw(self) -> bool:
        """Checks for a draw."""
        return "" not in self.board

    async def end_game(self, interaction: disnake.AppCommandInteraction) -> None:
        """Ends the game and disables the buttons."""
        for child in self.children:
            child.disabled = True
        await interaction.edit_original_message(view=self)

    async def handle_turn(
        self, button: disnake.ui.Button, interaction: disnake.AppCommandInteraction
    ) -> None:
        """
        Handles player turns.

        Args:
            button (disnake.ui.Button): The button that was clicked.
            interaction (disnake.AppCommandInteraction): The interaction that triggered the button click.
        """
        error_embed = CustomEmbed.error_embed(
            author=interaction.user,
        ).get_embed()
        if interaction.user != self.current_player:
            error_embed.title = "❌ | It's not your turn!"
            await interaction.response.send_message(
                embed=error_embed,
                ephemeral=True,
            )
            return

        index = button.index
        if self.board[index] != "":
            error_embed.title = "❌ | Cell already marked!"
            await interaction.response.send_message(
                embed=error_embed,
                ephemeral=True,
            )
            return

        self.board[index] = "X" if self.current_player == self.player1 else "O"
        button.label = "X" if self.current_player == self.player1 else "O"
        button.style = (
            disnake.ButtonStyle.danger
            if button.label == "X"
            else disnake.ButtonStyle.primary
        )
        button.disabled = True
        original_embed: disnake.Embed = interaction.message.embeds[0]

        if self.check_win():
            original_embed.set_author(
                name=f"{self.winner.display_name} won!",
                icon_url=self.winner.display_avatar.url,
            )
            await interaction.response.edit_message(
                content=f"{self.current_player.mention}",
                embed=original_embed,
                view=self,
            )
            await self.end_game(interaction)
            return

        if self.check_draw():
            original_embed.set_author(
                name=f"Draw", icon_url=interaction.author.display_avatar.url
            )
            await interaction.response.edit_message(
                content="",
                embed=original_embed,
                view=self,
            )
            await self.end_game(interaction)
            return

        self.current_player = (
            self.player2 if self.current_player == self.player1 else self.player1
        )
        original_embed.set_author(
            name=self.current_player.display_name,
            icon_url=self.current_player.display_avatar.url,
        )
        await interaction.response.edit_message(
            content=f"{self.current_player.mention}",
            embed=original_embed,
            view=self,
        )


class TicTacToeButton(disnake.ui.Button):
    def __init__(self, index):
        super().__init__(
            style=disnake.ButtonStyle.secondary, label="\u200b", row=index // 3
        )
        self.index = index

    async def callback(self, interaction: disnake.MessageInteraction):
        view: TicTacToeView = self.view
        await view.handle_turn(self, interaction)
