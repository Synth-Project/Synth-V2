import disnake
from disnake.ext import commands
from core.database.repositories.guild import GuildMusicRepository


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Settings, self).__init__()

        self.guild_music_repo = GuildMusicRepository()
        self.bot = bot

    @commands.slash_command()
    async def set_dj_role(
        self, interaction: disnake.ApplicationCommandInteraction, role: disnake.Role
    ):
        old_dj = await self.guild_music_repo.find_dj_role(guild_id=interaction.guild.id)

        if not old_dj or old_dj != role.id:
            await self.guild_music_repo.set_dj_role(
                guild_id=interaction.guild.id, role_id=role.id
            )

            print(
                await self.guild_music_repo.find_dj_role(guild_id=interaction.guild.id),
            )
        else:
            await interaction.response.send_message(
                "This role is already set as DJ role", ephemeral=True
            )

        # await self.guild_music_repo.set_dj_role(guild_id=interaction.guild.id, role_id=role.id)
        # await GuildMusicRepository().set_dj_role(
        #     guild_id=interaction.guild.id, role_id=role.id
        # )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Settings(bot))
