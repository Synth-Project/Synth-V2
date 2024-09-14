import glob
import os

import disnake
from disnake.ext import commands

from core.main.config.config import settings

from core.database import init_database, close_database
from core import logger


class Bot(commands.AutoShardedInteractionBot):
    """The base class of Synth bot."""

    def __init__(self) -> None:
        super(Bot, self).__init__(
            intents=disnake.Intents.all(),
            reload=True,
            owner_ids=settings.OWNERS,
            test_guilds=settings.TEST_GUILDS,
        )
        self.debug = settings.DEBUG
        self.logger = logger.bind(source=self.__class__.__module__)

    async def load_extensions(
        self, bot: commands.Bot, cogs_paths: list[str] = None
    ) -> None:
        stats = {
            "commands": {"loaded": [], "total": 0},
            "events": {"loaded": [], "total": 0},
            "autocomplete": {"loaded": [], "total": 0},
        }

        if not cogs_paths:
            cogs_paths = [
                "core/cogs/commands",
                "core/cogs/events",
                "core/cogs/autocomplete",
            ]

        for path in cogs_paths:
            category = (
                "commands"
                if "commands" in path
                else "events" if "events" in path else "autocomplete"
            )
            for file_path in glob.glob(os.path.join(path, "*.py")):
                file_name = os.path.basename(file_path)

                if file_name == "__init__.py":
                    continue

                extension_name = f"{path.replace('/', '.')}.{file_name[:-3]}"

                try:
                    bot.load_extension(extension_name)
                    stats[category]["loaded"].append(extension_name)
                    stats[category]["total"] += 1
                except (
                    commands.ExtensionNotFound,
                    commands.NoEntryPointError,
                    commands.ExtensionFailed,
                    commands.ExtensionError,
                    commands.ExtensionAlreadyLoaded,
                ) as e:
                    logger.error(f"[-] Error loading cog: {extension_name}")
                    import traceback

                    traceback.print_exception(type(e), e, e.__traceback__)

        for category in ["commands", "events", "autocomplete"]:
            if stats[category]["loaded"]:
                names = ", ".join(
                    [name.split(".")[-1] for name in stats[category]["loaded"]]
                )
                self.logger.info(
                    f"[%] Loaded {category}: {names} ({len(stats[category]['loaded'])}/{stats[category]['total']})"
                )

        total_loaded = len(stats["commands"]["loaded"]) + len(stats["events"]["loaded"])
        total_all = stats["commands"]["total"] + stats["events"]["total"]
        self.logger.info(f"[%] {total_loaded}/{total_all} cogs loaded")

    @staticmethod
    async def on_connect() -> None:
        await init_database()

    @staticmethod
    async def on_disconnect() -> None:
        await close_database()

    async def on_ready(self) -> None:
        logger.info(
            f"\nInvite link: https://discord.com/api/oauth2/authorize?client_id="
            f"{self.user.id}&permissions=980937982&scope=bot%20applications.commands"
        )
        logger.debug(f"Connected to {self.user}")

        await self.load_extensions(bot=self)
        await self.wait_until_ready()

        await self.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.custom,
                name=f"/help | v1.0",
                status=disnake.Status.idle,
            )
        )

    def get_avatar(self) -> str:
        """Returns the URL of the bot's avatar"""
        return "https://cdn.discordapp.com/avatars/1168226895758901408/8cc117b5f9a539896875e7a0b837c2ed.webp?size=1024&format=webp&width=0&height=256"
