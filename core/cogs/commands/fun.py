import disnake
from disnake.ext import commands
from core import logger

class FunCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(FunCommands, self).__init__()

        self.bot = bot

    @commands.slash_command(name="gay")
    async def gay(self, interaction: disnake.Interaction):
        text = """<:youtube:1279826494847451199>
<:soundcloud:1285240280135766058>
<:spotify:1284447177082408990>
<:applemusic:1285240602014908507>
<:deezer:1285240923432681483>
<:defmusic:1285241530705121325>"""
        await interaction.response.defer(ephemeral=True)
        # await interaction.channel.send(text)
        for i in range(2500):
            logger.debug("I'm gay")
            logger.error("I'm gay")
            logger.info("I'm sigmal")
        await interaction.send("gay")
        interaction.guild.shard_id

def setup(bot: commands.Bot) -> None:
    bot.add_cog(FunCommands(bot))
