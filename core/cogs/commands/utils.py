import disnake
from disnake.ext import commands

from core.misc.color import BasicColors

from core.misc.misc import create_ping_command_string


class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Utilities, self).__init__()
        self.bot = bot

    @commands.slash_command()
    async def hello(self, ineteraction: disnake.ApplicationCommandInteraction):
        for command in self.bot.slash_commands:
            if command.name == "player":
                print(
                    command.children
                )  # {'play': <disnake.ext.commands.slash_core.SubCommand object at 0x0000011DF4B31650>, 'skip': <disnake.ext.commands.slash_core.SubCommand object at 0x0000011DF5DB21D0>}
                for child in command.children:
                    print(f"{child}")  # play, skip


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utilities(bot))
