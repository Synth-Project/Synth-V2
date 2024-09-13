import disnake
from disnake.ext import commands

from core.misc.color import BasicColors

# from core.misc.music.functions import hello
from core.misc.music.functions import hello
from core.misc.embed import CustomEmbed

# import core.misc.music.functions as functions
# import core.misc.music.functions


class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Utilities, self).__init__()
        self.bot = bot

    @commands.slash_command()
    async def hello(self, ctx: disnake.ApplicationCommandInteraction):
        # ret = functions.hello()
        ret = hello()
        print(ret)

        await ctx.send(
            embed=CustomEmbed(title=ret, color=BasicColors.ERROR).get_embed()
        )
        # await ctx.send(ret)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utilities(bot))
