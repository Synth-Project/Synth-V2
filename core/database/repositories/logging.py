import disnake
from disnake.ext import commands
from core.database.models.logging import *
from core.database.repositories.base import BaseRepository
from typing import Any, Self


class LoggingRepository(BaseRepository):
    PREFETCH_FIELDS = [
        "member_logs",
        "message_logs",
        "reaction_logs",
        "guild_logs",
        "channel_logs",
        "role_logs",
    ]

    @staticmethod
    async def get_one(**kwargs) -> Logging | None:
        return await Logging.get_or_none(**kwargs).prefetch_related(
            *LoggingRepository.PREFETCH_FIELDS
        )

    @staticmethod
    async def get_all(**kwargs) -> list[Logging]:
        return (
            await Logging.filter(**kwargs)
            .prefetch_related(*LoggingRepository.PREFETCH_FIELDS)
            .all()
        )

    @staticmethod
    async def _get_logging(guild_id: int) -> Logging | None:
        return await Logging.get_or_none(guild_id=guild_id).prefetch_related(
            *LoggingRepository.PREFETCH_FIELDS
        )

    @staticmethod
    async def get_specific_logger(guild_id: int, logger_type: str) -> Any | None:
        logging = await LoggingRepository._get_logging(guild_id)
        return getattr(logging, f"{logger_type}_logs") if logging else None

    @staticmethod
    async def get_member_logger(guild_id: int) -> MemberLogging | None:
        return await LoggingRepository.get_specific_logger(guild_id, "member")

    @staticmethod
    async def get_message_logger(guild_id: int) -> MessageLogging | None:
        return await LoggingRepository.get_specific_logger(guild_id, "message")

    @staticmethod
    async def get_channel_logger(guild_id: int) -> ChannelLogging | None:
        return await LoggingRepository.get_specific_logger(guild_id, "channel")

    @staticmethod
    async def get_role_logger(guild_id: int) -> RoleLogging | None:
        return await LoggingRepository.get_specific_logger(guild_id, "role")

    @staticmethod
    async def get_guild_logger(guild_id: int) -> GuildLogging | None:
        return await LoggingRepository.get_specific_logger(guild_id, "guild")

    @staticmethod
    async def get_reaction_logger(guild_id: int) -> ReactionLogging | None:
        return await LoggingRepository.get_specific_logger(guild_id, "reaction")

    @staticmethod
    async def add_one(**kwargs) -> tuple[Logging, bool]:
        return await Logging.get_or_create(**kwargs)

    @staticmethod
    async def remove_one(**kwargs):
        return await Logging.filter(**kwargs).delete()

    @staticmethod
    async def _get_or_create_logging(guild_id: int) -> Logging:
        logging = await LoggingRepository._get_logging(guild_id)
        if logging:
            return logging

        log_types = {
            "member": MemberLogging,
            "message": MessageLogging,
            "reaction": ReactionLogging,
            "guild": GuildLogging,
            "channel": ChannelLogging,
            "role": RoleLogging,
        }

        logs = {f"{k}_logs": await v.create() for k, v in log_types.items()}
        await Logging.create(guild_id=guild_id, **logs)

        return await Logging.get(guild_id=guild_id).prefetch_related(
            *LoggingRepository.PREFETCH_FIELDS
        )

    @staticmethod
    async def _change_logger(guild_id: int, logger_type: str, model_class, **kwargs):
        logging = await LoggingRepository._get_or_create_logging(guild_id)
        logger = getattr(logging, f"{logger_type}_logs")
        await model_class.filter(id=logger.id).update(**kwargs)
        return await model_class.get(id=logger.id)

    @staticmethod
    async def change_member_logger(guild_id: int, **kwargs):
        return await LoggingRepository._change_logger(
            guild_id, "member", MemberLogging, **kwargs
        )

    @staticmethod
    async def change_message_logger(guild_id: int, **kwargs):
        return await LoggingRepository._change_logger(
            guild_id, "message", MessageLogging, **kwargs
        )

    @staticmethod
    async def change_channel_logger(guild_id: int, **kwargs):
        return await LoggingRepository._change_logger(
            guild_id, "channel", ChannelLogging, **kwargs
        )

    @staticmethod
    async def change_role_logger(guild_id: int, **kwargs):
        return await LoggingRepository._change_logger(
            guild_id, "role", RoleLogging, **kwargs
        )

    @staticmethod
    async def change_guild_logger(guild_id: int, **kwargs):
        return await LoggingRepository._change_logger(
            guild_id, "guild", GuildLogging, **kwargs
        )

    @staticmethod
    async def change_reaction_logger(guild_id: int, **kwargs):
        return await LoggingRepository._change_logger(
            guild_id, "reaction", ReactionLogging, **kwargs
        )

    async def get_channel(
        self, bot: commands.Bot, guild_id: int, event_type: str
    ) -> tuple[disnake.TextChannel | None, Self | None]:
        result = await self.get_member_logger(guild_id=guild_id)
        if not result or not getattr(result, f"{event_type}_event", None):
            return None, None

        try:
            channel_id = getattr(result, f"{event_type}_event_channel_id")
            channel = bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
            return channel, result
        except (disnake.NotFound, disnake.Forbidden):
            return None, None
