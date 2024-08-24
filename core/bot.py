import logging

import disnake
from disnake.ext import commands

from core.main.config.config import settings

from core.database import init_database, close_database


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

        await self.wait_until_ready()
        await self.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.competing,
                name=f"/help | v1.0",
                status=disnake.Status.idle,
            )
        )
