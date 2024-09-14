import random
from typing import Optional

import aiohttp
import disnake
from disnake.ext import commands, tasks

from loguru import logger
from core.bot import Bot


class FunCommands(commands.Cog):
    def __init__(self, bot: "Bot") -> None:
        self.bot = bot
        self.cache: dict[str, list[str]] = {"cat": [], "dog": [], "fox": []}
        self.logger = logger.bind(source=self.__class__.__module__)

    async def cog_load(self) -> None:
        self.update_all_cache.start()

    def cog_unload(self) -> None:
        self.update_all_cache.stop()

    async def update_cache(
        self,
        subreddit: str,
        media_type: tuple[str, ...] = ("jpg", "png", "jpeg", "gif", "mp4"),
    ) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://www.reddit.com/r/{subreddit}.json?limit=100",
                headers={
                    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
                },
            ) as response:
                if response.status != 200:
                    logger.info(f"An error occurred while getting data for {subreddit}")
                    return

                data = await response.json()
                posts = data["data"]["children"]

                for post in posts:
                    if (
                        (post := post["data"]["url"])
                        and post.endswith(media_type)
                        and post not in self.cache[subreddit]
                    ):
                        self.cache[subreddit].append(post)

                self.bot.debug and self.logger.debug(
                    f"[+] Updated cache for {subreddit}, found {len(self.cache[subreddit])} elements."
                )

    async def get_random_image_from_cache(self, subreddit: str) -> Optional[str]:
        if self.cache[subreddit]:
            return random.choice(self.cache[subreddit])
        return None

    @tasks.loop(hours=1)
    async def update_all_cache(self) -> None:
        self.logger.info("[~] Updating images cache...")
        await self.update_cache("cat")
        await self.update_cache("dog")
        await self.update_cache("fox")
        self.logger.info("[+] Updated all cache")

    @update_all_cache.before_loop
    async def before_update_all_cache(self) -> None:
        await self.bot.wait_until_ready()

    @commands.slash_command(description="Retrieve a random cat image from r/cat")
    async def cat(self, inter: disnake.ApplicationCommandInteraction) -> None:
        image_url = await self.get_random_image_from_cache("cat")
        if image_url:
            await inter.response.send_message(image_url)
        else:
            await inter.response.send_message("Cannot find any cat images.")

    @commands.slash_command(description="Retrieve a random dog image from r/dog")
    async def dog(self, inter: disnake.ApplicationCommandInteraction) -> None:
        image_url = await self.get_random_image_from_cache("dog")
        if image_url:
            await inter.response.send_message(image_url)
        else:
            await inter.response.send_message("Cannot find any dog images.")

    @commands.slash_command(description="Retrieve a random fox image from r/fox")
    async def fox(self, inter: disnake.ApplicationCommandInteraction) -> None:
        image_url = await self.get_random_image_from_cache("fox")
        if image_url:
            await inter.response.send_message(image_url)
        else:
            await inter.response.send_message("Cannot find any fox images.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(FunCommands(bot))
