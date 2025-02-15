from typing import Union

import disnake
from disnake.ext import commands

from core.misc.embed import CustomEmbed
from core.misc.misc import mention_slash


class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Utilities, self).__init__()
        self.bot = bot

    @commands.slash_command()
    async def hello(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.send(content=mention_slash(interaction.guild, "player play"))  # type: ignore

    @commands.slash_command(name="clear", description="Clear messages from chat")
    async def _clear_messages(
        self,
        interaction: disnake.MessageCommandInteraction,
        message_count: int,
        channel: disnake.TextChannel = commands.Param(
            name="channel",
            description="The channel to clear messages from",
            default=None,
        ),
        target_user: Union[disnake.User, disnake.Member] = commands.Param(
            name="user", description="The user to clear messages from", default=None
        ),
        silent_mode: bool = commands.Param(
            name="--silent", description="Silent mode", default=False
        ),
    ) -> None:
        channel = channel or interaction.channel

        if message_count > 100:
            message_count = 100

        try:
            await channel.trigger_typing()

            if target_user:
                deleted_messages = await channel.purge(
                    limit=message_count,
                    check=lambda m: m.author == target_user,
                )
            else:
                deleted_messages = await channel.purge(
                    limit=message_count,
                )
        except (disnake.Forbidden, disnake.HTTPException):
            await interaction.send(
                embed=CustomEmbed.error_embed(
                    description="Sorry, the bot doesn't have enough permissions to delete messages",
                ).get_embed(),
                delete_after=10,
                ephemeral=silent_mode,
            )
            return

        await interaction.response.defer(ephemeral=silent_mode)

        embed = CustomEmbed(
            title="<a:loading:1168599537682755584> Cleaning messages...",
            description=f"Deleted `{len(deleted_messages)}` messages",
        ).get_embed()
        await interaction.send(embed=embed, delete_after=10, ephemeral=silent_mode)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utilities(bot))
