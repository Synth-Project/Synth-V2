import random
from typing import Optional

import aiohttp
import disnake
from disnake.ext import commands, tasks

from loguru import logger
from core.bot import Bot
from core.misc.embed import CustomEmbed
from core.misc.fun.views.tictactoe import ConfirmView, TicTacToeView


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
            embed = CustomEmbed(title="😺 | Cat").get_embed().set_image(image_url)
            await inter.response.send_message(embed=embed)
        else:
            error_embed = CustomEmbed.error_embed(
                title="❌ | Cannot find any cat images."
            )
            await inter.response.send_message(embed=error_embed)

    @commands.slash_command(description="Retrieve a random dog image from r/dog")
    async def dog(self, inter: disnake.ApplicationCommandInteraction) -> None:
        image_url = await self.get_random_image_from_cache("dog")
        if image_url:
            embed = CustomEmbed(title="🐶 | Dog").get_embed().set_image(image_url)
            await inter.response.send_message(embed=embed)
        else:
            error_embed = CustomEmbed.error_embed(
                title="❌ | Cannot find any dog images."
            )
            await inter.response.send_message(embed=error_embed)

    @commands.slash_command(description="Retrieve a random fox image from r/fox")
    async def fox(self, inter: disnake.ApplicationCommandInteraction) -> None:
        image_url = await self.get_random_image_from_cache("fox")
        if image_url:
            embed = CustomEmbed(title="🦊 | Fox").get_embed().set_image(image_url)
            await inter.response.send_message(embed=embed)
        else:
            error_embed = CustomEmbed.error_embed(
                title="❌ | Cannot find any fox images."
            )
            await inter.response.send_message(embed=error_embed)

    @commands.slash_command(description="Pop-it game")
    async def popit(self, interaction: disnake.ApplicationCommandInteraction) -> None:
        pop_it = """
🔴🔴🔴🔴🔴🔴
🟡🟡🟡🟡🟡🟡
🔵🔵🔵🔵🔵🔵
🟢🟢🟢🟢🟢🟢
🟤🟤🟤🟤🟤🟤
🟣🟣🟣🟣🟣🟣
        """
        embed = CustomEmbed(
            title="👆 | Pop-it",
            description=self.add_spoilers(pop_it),
        ).get_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def add_spoilers(self, text):
        return "".join(f"||{char}||" if char.strip() else char for char in text)

    @commands.slash_command()
    async def simple(self, _):
        pass

    @simple.sub_command(description="Simple dimple")
    async def dimple(self, interaction: disnake.ApplicationCommandInteraction) -> None:
        dimple = """
⚫⚫⚫
⚫||🔵||⚫
⚫⚫⚫
⚫||🟡||⚫
⚫⚫⚫
        """
        embed = CustomEmbed(
            title="👆 | Simple Dimple",
            description=dimple,
        ).get_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command()
    async def url(self, _):
        pass

    @url.sub_command(description="Shorten a URL")
    async def shorten(
        self, interaction: disnake.ApplicationCommandInteraction, url: str
    ) -> None:
        """
        Shorten a URL using TinyURL.
        """
        short_url_embed = CustomEmbed(
            title="🔗 | Shorten URL",
            description="",
        ).get_embed()
        error_embed = CustomEmbed.error_embed(
            title="❌ | An error occurred while shortening the URL",
        ).get_embed()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://tinyurl.com/api-create.php?url={url}"
            ) as response:
                if response.status == 200:
                    short_url = await response.text()
                    short_url_embed.description = short_url
                    await interaction.response.send_message(
                        embed=short_url_embed, ephemeral=True
                    )
                    return

        await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @url.sub_command(description="Unshorten a URL")
    async def unshorten(
        self, interaction: disnake.ApplicationCommandInteraction, url: str
    ) -> None:
        embed = CustomEmbed(title="🔗 | Unshorten URL").get_embed()
        error_embed = CustomEmbed.error_embed(
            title="❌ | An error occurred while unshortening the URL"
        ).get_embed()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://unshorten.me/api/v2/unshorten?url={url}",
                headers={
                    "Authorization": "Token 9cdfabb415e6c1ae83f9e371b9b08f7e18a9f362"
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and data.get("unshortened_url"):
                        embed.description = data["unshortened_url"]
                        await interaction.response.send_message(
                            embed=embed, ephemeral=True
                        )
                        return

        await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @commands.slash_command()
    async def tic_tac_toe(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        opponent: disnake.Member,
    ) -> None:
        error_embed = CustomEmbed.error_embed(
            author=interaction.author,
        ).get_embed()
        embed = CustomEmbed(
            title="🎮 | Tic-Tac-Toe", author=interaction.author
        ).get_embed()
        if opponent.bot:
            error_embed.title = "❌ | You can't play Tic-Tac-Toe with a bot."
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        if opponent == interaction.user:
            error_embed.title = "❌ | You can't play Tic-Tac-Toe with yourself."
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        embed.description = f"Do you want to play Tic-Tac-Toe with {interaction.author.name}? You have 3 minutes to respond."
        view = ConfirmView(confirmer=opponent)
        await interaction.response.send_message(
            f"{opponent.mention}", embed=embed, view=view
        )
        await view.wait()

        if view.value is None:
            error_embed.title = f"❌ | Opponent didn't respond in time. Game cancelled."
            await interaction.edit_original_response(embed=error_embed, view=None)
            return
        elif view.value is False:
            error_embed.title = f"❌ | Opponent declined the game. Game cancelled."
            await interaction.edit_original_response(embed=error_embed, view=None)
            return

        game_view = TicTacToeView(interaction.user, opponent)
        embed.description = (
            f"**{interaction.author.name}** (X) vs **{opponent.name}** (O)!"
        )
        await interaction.edit_original_response(
            f"{interaction.user.mention}",
            embed=embed,
            view=game_view,
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(FunCommands(bot))
