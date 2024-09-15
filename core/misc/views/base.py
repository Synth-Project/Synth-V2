import disnake

class CustomButton(disnake.ui.Button):
    def __init__(self, row: int = 0, **kwargs):
        super().__init__(
            label="Back",
            style=disnake.ButtonStyle.red,
            custom_id="back",
            row = row
        )
        self.kwargs = kwargs

    async def callback(self, interaction: disnake.MessageInteraction):
        await interaction.response.edit_message(**self.kwargs)