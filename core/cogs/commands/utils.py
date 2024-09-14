import asyncio
import datetime
import sys
from typing import Union

import disnake
from disnake.ext import commands, tasks
from memory_profiler import memory_usage

from core.database.models.reminder import Remind, ReminderType
from core.database.repositories.birthday import BirthdayRepository
from core.database.repositories.reminder import ReminderRepository
from core.misc.embed import CreatePaginator, custom_embed
from core.misc.emoji import StandartEmoji
from core.misc.util.misc import generate_time_options, shorten_text
from core.misc.util.views.main import MainReminderView

startup = datetime.datetime.now()


class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Utilities, self).__init__()
        self.bot = bot
        self.badges = {
            1: "<:staff:1168622635228344403>",
            2: "<:partner:1168622631705137233>",
            4: "<:hypesquad:1168622629901586605>",
            8: "<:bug_hunter:1168622622045634622>",
            64: "<:hypersquad_bravery:1168622644455805100>",
            128: "<:hypersquad_brilliance:1168622642690015373>",
            256: "<:hypersquad_balance:1168622640240533514>",
            512: "<:early_supporter:1168622625896009729>",
            1024: "<:team_user:1168622638592163991>",
            16384: "<:bug_hunter:1168622622045634622>",
            65536: "<:developer:1168622649967116378>",
            131072: "<:developer:1168622649967116378>",
            262144: "<:shield:1168250173089140956>",
            1048576: "⚠️",
            133172312: "<:synthdev:1169689479452311582>",
        }

    async def cog_load(self):
        self.check_reminds.start()

    async def _get_message(self, channel_id: int):
        """Fetch a channel and return whether it was successful."""
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
            return channel
        except disnake.HTTPException:
            return False

    async def remind(self, remind: Remind):
        user_model = await ReminderRepository().get_one(reminds=remind)
        if remind.type == ReminderType.DM:
            channel = await self.bot.getch_user(user_model.id)
        else:
            channel = await self._get_message(remind.channel_id)

        if not channel:
            await Remind.delete(remind)
            return

        embed = custom_embed("Reminder", remind.text)

        if isinstance(channel, (disnake.User, disnake.Member)):
            try:
                await channel.send(embed=embed)
            except:
                await Remind.delete(remind)
        else:
            await channel.send(content=f"<@{user_model.id}>", embed=embed)

        await Remind.delete(remind)

    @tasks.loop(seconds=1)
    async def check_reminds(self):
        result = await ReminderRepository().get_all_reminds()
        if result:
            for remind in result:
                if remind.time <= datetime.datetime.now().timestamp():
                    await self.remind(remind)

    @commands.slash_command(name="server")
    async def server(
        self,
        interaction,
        silent: bool = commands.Param(
            name="--silent", description="Silent mode", default=False
        ),
    ):
        emoji_count = len(interaction.guild.emojis)
        list_of_bots = len([m for m in interaction.guild.members if m.bot])
        list_of_users = len([m for m in interaction.guild.members if not m.bot])
        guild_created_at = disnake.utils.format_dt(
            interaction.guild.created_at, style="f"
        )
        text_channels = len(interaction.guild.text_channels)
        voice_channels = len(interaction.guild.voice_channels)
        categories = len(interaction.guild.categories)
        threads = len(interaction.guild.threads)
        owner = interaction.guild.owner

        embed = custom_embed(
            f"<:info:1169685342077583480> {interaction.guild.name}'s information",
            description=interaction.guild.description or "No description",
        )
        embed.add_field(
            name="Main Information",
            value=(
                f"<:owner:1169684595697004616> Owner: {owner.mention} (`{owner.id}`)\n"
                f"<:id:1169690511536312340> Server ID: `{interaction.guild.id}`\n"
                f"<:created_at:1169684592006017034> Created at: {guild_created_at}\n"
                f"<:boost:1169685353515462697> Boosts: `{interaction.guild.premium_subscription_count}`\n"
                f"<:star:1169685347576336385> Emojis: `{emoji_count}`\n"
                f"<:link:1169685349409226893> Icon: [`click`]({interaction.guild.icon})\n"
                f"<:channels:1169684589640429599> Channels: `{len(interaction.guild.channels)}`\n"
                f"<:design:1169686174374301746> <:channels:1169684589640429599> Text Channels: `{text_channels}`\n"
                f"<:design:1169686174374301746> <:voice:1169684588315029534> Voice Channels: `{voice_channels}`\n"
                f"<:design:1169686174374301746> <:category:1169684586666663999> Categories: `{categories}`\n"
                f"<:design:1169688944502378536> <:thread:1169685355423866963> Threads: `{threads}`\n\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Members",
            value=f"<:members:1169684583369949285> All members: `{len(interaction.guild.members)}`\n"
            f"<:design:1169686174374301746> <:members:1169684583369949285> Human: `{list_of_users}`\n"
            f"<:design:1169688944502378536> <:bot:1169685346506776697> Bots: `{list_of_bots}`",
            inline=False,
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.set_image(url=interaction.guild.banner)
        await interaction.send(embed=embed, ephemeral=silent)

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
            deleted_messages = await channel.purge(
                limit=message_count,
                check=lambda m: m.author == target_user if target_user else None,
            )
        except (disnake.Forbidden, disnake.HTTPException):
            await interaction.send(
                embed=custom_embed(
                    description="Sorry, the bot doesn't have enough permissions to delete messages",
                    color=disnake.Color.red(),
                ),
                delete_after=10,
                ephemeral=silent_mode,
            )
            return

        await interaction.response.defer(ephemeral=silent_mode)

        embed = custom_embed()
        embed.title = "<a:loading:1168599537682755584> Cleaning messages..."
        embed.description = f"Deleted `{len(deleted_messages)}` messages"
        await interaction.send(embed=embed, delete_after=10, ephemeral=silent_mode)

    @commands.slash_command(
        name="bot", description="Display information about the bot.", aliases=["synth"]
    )
    async def _bot_info(
        self,
        interaction: disnake.MessageCommandInteraction,
        silent: bool = commands.Param(
            name="--silent", description="Silent mode", default=False
        ),
    ):
        channels = set(self.bot.get_all_channels())
        big_builds = len([g for g in self.bot.guilds if g.member_count >= 1000])

        embed = custom_embed(
            title="Information about Synth",
            description="**Synth** - is a multi-functional Discord bot.",
        ).set_thumbnail(url=self.bot.user.avatar)
        embed.add_field(
            name="Main",
            value=f"<:clock:1169690592465395722> Ping: `{round(self.bot.latency * 1000)}` ms\n"
            f"<:activities:1169690504393404456> RAM: `{round(memory_usage()[0], 2)}` mb\n"
            f"<:icons_goodping:1169690518645649478> Uptime: {disnake.utils.format_dt(startup, style='F')}\n",
            inline=False,
        )
        embed.add_field(
            name="Popularity",
            value=f"<:info:1169685342077583480> Servers: `{len(self.bot.guilds)}`\n"
            f"<:globe:1169690501063123065> Big servers (1000+): `{big_builds}`\n"
            f"<:members:1169684583369949285> Users: `{len(set(self.bot.get_all_members()))}`\n"
            f"<:channels:1169684589640429599> Channels: `{len(channels)}`\n",
            inline=False,
        )
        embed.add_field(
            name="Other Information",
            value=f"<:calendar:1169690539168366712> Created at: `31/10/2023`\n"
            f"<:created_at:1169684592006017034> Bot version: `v2.0.0`\n"
            f"<:wrench:1169690509929889802> Python version: `{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}`\n"
            f"<:owner:1169684595697004616> Owners: [Nixxoq](https://discord.com/users/999682446675161148), "
            f"[Weever](https://discord.com/users/419159175009009675), "
            f"[LazyDev](https://discord.com/users/1256533103967735811)",
            inline=False,
        )

        support = disnake.ui.Button(
            label="Support server", url="https://discord.gg/7vT3H3tVYp"
        )
        website = disnake.ui.Button(
            label="Documentation", url="https://synth.gitbook.io/"
        )

        await interaction.send(
            embed=embed, components=[support, website], ephemeral=silent
        )

    @commands.slash_command(name="user", description="Display information about user.")
    async def user(
        self,
        interaction: disnake.MessageCommandInteraction,
        user: Union[disnake.User, disnake.Member] = commands.Param(
            description="Choice user",
            name="user",
            default=None,
        ),
        silent: bool = commands.Param(
            name="--silent", description="Silent mode", default=False
        ),
    ) -> None:
        user = user or interaction.user
        embed = custom_embed(
            title=f"<:members:1169684583369949285> {user.name}'s information",
            description=f"<:link:1169685349409226893> [Link to DM](discord://discord.com/users/{user.id})",
        )
        value = (
            f"<:info:1169685342077583480> ID: `{user.id}`\n"
            f"<:created_at:1169684592006017034> Created at: {disnake.utils.format_dt(user.created_at, style='f')}\n"
        )

        embed.set_thumbnail(
            url=(
                user.display_avatar.url
                if user.display_avatar
                else user.avatar.url if user.avatar else None
            )
        )
        embed.set_image(url=user.banner.url if user.banner else None)

        if isinstance(user, disnake.Member):
            value += (
                f"<:info:1169685342077583480> Joined at: {disnake.utils.format_dt(user.joined_at, style='f')}\n"
                f"<:activities:1169690504393404456> Status: `{str(user.status).upper()}`\n"
                f"<:globe:1169690501063123065> Is on mobile?: `{str(user.is_on_mobile()).upper()}`\n"
                f"<:globe:1169690501063123065> Booster?: `{str(user.premium_since is not None).upper()}`\n"
                f"<:design:1169688944502378536> Top role: {user.top_role.mention}\n"
                f"<:design:1169688944502378536> Roles: {', '.join([role.mention for role in user.roles if not role.is_default() and role.name != '@everyone'])}\n"
            )

        embed.add_field(name="Main information", value=value, inline=False)

        flags = " ".join(
            [
                user_badges
                for badge, user_badges in self.badges.items()
                if user.public_flags._has_flag(badge)
            ]
        )

        if flags:
            embed.add_field(
                name="<:list:1169690529643114547> Flags", value=flags, inline=False
            )

        await interaction.send(embed=embed, ephemeral=silent)

    @commands.slash_command()
    async def reminder(self, _):
        pass

    @reminder.sub_command(name="create", description="Create a reminder")
    async def create(
        self,
        inter: disnake.MessageCommandInteraction,
        text: str = commands.Param(name="text"),
        time: int = commands.Param(autocomplete=True),
    ):
        embed = custom_embed(
            "Reminder", "Select the method of reminder message", author=inter.author
        )
        embed.add_field(name="Text", value=text, inline=True)
        embed.add_field(name="Time", value=time, inline=True)
        await inter.response.send_message(
            embed=embed, ephemeral=True, view=MainReminderView(self.bot, time, text)
        )

    @create.autocomplete("time")
    async def time_autocomplete(
        self, inter: disnake.MessageCommandInteraction, string: str
    ):
        if not string:
            string = "15"

        options = generate_time_options(string.lower())

        if not options:
            try:
                number = int(string)
                if number > 0:
                    options = [
                        disnake.OptionChoice(
                            name=f"{number} seconds", value=str(number)
                        ),
                        disnake.OptionChoice(
                            name=f"{number} minutes", value=str(number * 60)
                        ),
                        disnake.OptionChoice(
                            name=f"{number} hours", value=str(number * 3600)
                        ),
                        disnake.OptionChoice(
                            name=f"{number} days", value=str(number * 86400)
                        ),
                    ]
            except ValueError:
                return []

        await inter.response.autocomplete(choices=options)

    @reminder.sub_command(description="List of all your reminders")
    async def list(self, inter: disnake.MessageCommandInteraction):
        result = await ReminderRepository().get_all_reminds()
        if not result:
            return await inter.response.send_message(
                f"{StandartEmoji.DENY.value} **{inter.author.name}**, You don't have any reminders",
                ephemeral=True,
            )

        reminders_list = [
            f"- **{shorten_text(remind.text, 10)}**\n - Time: {disnake.utils.format_dt(remind.time, style='R')}\n - Type: {str(remind.type.value).capitalize()}"
            for remind in result
            if result
        ]
        total_reminders = len(reminders_list)

        embeds = CreatePaginator.generate_embeds(
            items=reminders_list,
            items_per_embed=10,
            empty_list_message="You don't have any reminders",
            title="Reminder",
            description=f"Total reminders: **{total_reminders}**",
        )

        await inter.send(
            embed=embeds[0],
            view=CreatePaginator(embeds, inter.author.id, 120),
            ephemeral=True,
        ) 

    @commands.slash_command(name="birthday", description="Show your birthday status")
    async def birthday(self, inter: disnake.MessageCommandInteraction):
        result = await BirthdayRepository().get_one(id=inter.author.id)
        if not result:
            result = await BirthdayRepository().save_birthday(
                author_id=inter.author.id, day=9, month=11
            )
        print(result.birthday.day)
        await inter.send(f"Your birthday is on **{result.birthday.day}/{result.birthday.month}**")

    def check_if_user_is_developer(self, user_id: int) -> bool:
        return user_id in self.bot.owner_ids


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utilities(bot))
