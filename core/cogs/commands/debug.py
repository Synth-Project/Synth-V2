from disnake.ext import commands
import disnake
from core.database.repositories.logging import LoggingRepository


class Debug(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Debug, self).__init__()
        self.bot = bot

    def _get_logger_method(self, type_of_log: str):
        return {
            "member": LoggingRepository.change_member_logger,
            "guild": LoggingRepository.change_guild_logger,
            "message": LoggingRepository.change_message_logger,
            "role": LoggingRepository.change_role_logger,
            "reaction": LoggingRepository.change_reaction_logger,
            "channel": LoggingRepository.change_channel_logger,
        }.get(type_of_log.lower())

    @commands.slash_command(name="debug")
    async def debug(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        channel_to_log: disnake.TextChannel = commands.Param(
            description="Channel to send logs to"
        ),
        type_of_log: str = commands.Param(
            description="Type of log",
            choices=["member", "guild", "message", "role", "reaction", "channel"],
        ),
        type_of_event: str = commands.Param(
            description="Type of events to log",
            choices=["join", "leave", "update", "ban", "unban", "create", "delete", "remove", "add", "clear"],
        ),
    ) -> None:
        logger_method = self._get_logger_method(type_of_log)
        if not logger_method:
            return

        event_kwargs = {
            f"{type_of_event}_event": True,
            f"{type_of_event}_event_channel_id": channel_to_log.id,
        }

        if type_of_log == "member" and type_of_event == "ban":
            event_kwargs.update(
                {
                    "ban_event_reason": None,
                    "ban_event_moderator": None,
                }
            )

        await logger_method(guild_id=channel_to_log.guild.id, **event_kwargs)
        await interaction.response.send_message(
            f"✅ Successfully set up {type_of_log} {type_of_event} logging in {channel_to_log.mention}",
            ephemeral=True,
        )

    # @commands.slash_command()
    # @commands.contexts(bot_dm=True, private_channel=True, guild=True)
    # @commands.install_types(user=True, guild=True)
    # async def test(self, interaction: disnake.ApplicationCommandInteraction) -> None:
    #     s: disnake.Message = await interaction.channel.send("govno")
    #     s = await interaction
    #     await s.forward(channel=interaction.channel)

    # async def


def setup(bot: commands.Bot) -> None:

    bot.add_cog(Debug(bot))
