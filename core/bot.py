import logging
import os

import disnake
from disnake.ext import commands

from core.main.config.config import settings

from core.database import init_database, close_database

import traceback


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
        self.debug = False

    async def load_extensions(bot: commands.Bot, cogs_paths: list[str] = None) -> None:
        loaded = total = 0

        if not cogs_paths:
            cogs_paths = ["core/cogs/commands", "core/cogs/events"]

        for path in cogs_paths:
            for file in os.listdir(path):
                if not file.endswith(".py"):
                    continue

                total += 1

                try:
                    bot.load_extension(f"{path.replace('/', '.')}.{file[:-3]}")
                    loaded += 1
                    logging.info(f"Loaded cog: {file[:-3]}")
                except (
                    commands.ExtensionNotFound,
                    commands.NoEntryPointError,
                    commands.ExtensionFailed,
                    commands.ExtensionError,
                ) as e:
                    logging.info(f"- Error loading cog: {file[:-3]}\n\n")
                    # traceback.print_exception(e)

        logging.info(f"# {loaded}/{total} cogs loaded")

    async def on_connect(self) -> None:
        await init_database()

    async def on_disconnect(self) -> None:
        await close_database()

    async def on_ready(self) -> None:
        print("Started")
        logging.info(
            f"Invite link: https://discord.com/api/oauth2/authorize?client_id="
            f"{self.user.id}&permissions=980937982&scope=bot%20applications.commands"
        )
        logging.debug(f"Connected to {self.user}")

        await self.load_extensions()

        await self.wait_until_ready()
        await self.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.competing,
                name=f"/help | v1.0",
                status=disnake.Status.idle,
            )
        )
