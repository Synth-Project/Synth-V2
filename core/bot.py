import glob
import os

import disnake
from disnake.ext import commands

from core.database import init_database, close_database
from core.logger.logger import logger
from core.main.config.config import settings


class Bot(commands.AutoShardedInteractionBot):
    """The base class of Synth bot."""

    def __init__(self: "Bot") -> None:
        super(Bot, self).__init__(
            # help_command=CustomHelpCommand(),
            intents=disnake.Intents.all(),
            reload=True,
            owner_ids=settings.OWNERS,
            test_guilds=settings.TEST_GUILDS,
        )
        self.debug = settings.DEBUG

    async def load_extensions(self: commands.Bot, cogs_paths: list[str] = None) -> None:
        loaded = total = 0

        if not cogs_paths:
            cogs_paths = ["core/cogs/commands", "core/cogs/events"]

        for path in cogs_paths:
            for file_path in glob.glob(os.path.join(path, "*.py")):
                file_name = os.path.basename(file_path)
                if file_name == "__init__.py":
                    continue

                total += 1
                extension_name = f"{path.replace('/', '.')}.{file_name[:-3]}"

                try:
                    self.load_extension(extension_name)
                    loaded += 1
                    logger.info(f"[+] Loaded cog: {extension_name}")
                except (
                    commands.ExtensionNotFound,
                    commands.NoEntryPointError,
                    commands.ExtensionFailed,
                    commands.ExtensionError,
                ) as e:
                    logger.error(f"[-] Error loading cog: {extension_name}")
                    import traceback

                    traceback.print_exception(type(e), e, e.__traceback__)

        logger.info(f"[#] {loaded}/{total} cogs loaded")

    async def on_connect(self) -> None:
        await init_database()

    async def on_disconnect(self) -> None:
        await close_database()

    async def on_ready(self) -> None:
        logger.info(
            f"[#] Invite link: https://discord.com/api/oauth2/authorize?client_id="
            f"{self.user.id}&permissions=980937982&scope=bot%20applications.commands"
        )
        logger.info(f"[#] Connected to {self.user}")

        await self.load_extensions()
        await self.wait_until_ready()

        await self.change_presence(
            activity=disnake.Activity(
                name="Synth V2", type=disnake.ActivityType.custom, state=f"/help | v2.0"
            )
        )
