from disnake.ext import commands


class FunCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(FunCommands, self).__init__()

        self.bot = bot

    @commands.slash_command(name="gay")
    async def gay(self, interaction):
        await interaction.send("gay")

def setup(bot: commands.Bot) -> None:
    bot.add_cog(FunCommands(bot))
