import disnake
from disnake.ext import commands

from core.database.repositories import VoiceRoomsRepository
from core.database.models import VoiceRoom
from core.misc.embed import custom_embed


class KickUsersSelect(disnake.ui.Select):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: VoiceRoomsRepository,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel

        options = []

        for member in channel.members:
            options.append(
                disnake.SelectOption(
                    label=member.name,
                    value=str(member.id),
                    emoji="<:kick:1170712514288435271>",
                )
            )

        super().__init__(
            placeholder="Select participants to kick",
            min_values=1,
            max_values=len(channel.members),
            options=options,
            custom_id="kick",
        )

    async def callback(self, inter: disnake.MessageInteraction):
        main_room = await self.voices.get_private_room(guild_id=inter.guild_id)
        result: Optional[VoiceRoom] = await self.voices.get_room(main_room, self.channel.id)
        if result and result.id == self.channel.id:
            for _ in self.values:
                member = inter.guild.get_member(int(self.values[0]))
                if member.voice.channel == self.channel:
                    await member.move_to(channel=None)  # type: ignore
            await inter.send("Successfully kicked users", ephemeral=True)


class SetChannelName(disnake.ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
    ):
        self.bot = bot
        self.channel = channel
        self.values = {}

        super().__init__(
            title="New Channel Name",
            custom_id="channel_name",
            components=[
                disnake.ui.TextInput(
                    label="Channel Name",
                    custom_id="channel_name",
                    required=True,
                ),
            ],
        )

    async def callback(self, inter: disnake.ModalInteraction):
        new_channel_name = inter.text_values.get("channel_name", inter.channel.name)

        await self.channel.edit(name=new_channel_name)

        embed = custom_embed(
            title="Changing Channel Name",
            description=f"Successfully changed to: **{new_channel_name}**",
        )
        await inter.send(embed=embed, ephemeral=True)


class SetUserLimit(disnake.ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
    ):
        self.bot = bot
        self.channel = channel
        self.values = {}

        super().__init__(
            title="New Channel Limit",
            custom_id="channel_limit",
            components=[
                disnake.ui.TextInput(
                    label="New Limit",
                    custom_id="channel_limit",
                    placeholder="5",
                    required=True,
                ),
            ],
        )

    async def callback(self, inter: disnake.MessageInteraction):
        new_channel_limit = inter.text_values.get(
            "channel_limit", inter.channel.user_limit
        )

        await self.channel.edit(user_limit=int(new_channel_limit))

        embed = custom_embed(
            title="Room Limit",
            description=f"Successfully changed to: **{new_channel_limit}**",
        )
        await inter.send(embed=embed, ephemeral=True)


class BitrateSelect(disnake.ui.Select):
    def __init__(
        self,
        channel: disnake.VoiceChannel,
    ):
        self.channel = channel
        options = [
            disnake.SelectOption(
                label="8 kbps",
                value="8",
            ),
            disnake.SelectOption(
                label="64 kbps",
                value="64",
            ),
            disnake.SelectOption(
                label="96 kbps",
                value="96",
            ),
        ]
        super().__init__(
            placeholder="Choose a region",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="bitrate",
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        if int(self.values[0]) < 8 or int(self.values[0]) > 96:
            bitrate: int = int(self.values[0])
            await self.channel.edit(bitrate=bitrate)
        await inter.delete_original_response()


class RegionSelect(disnake.ui.Select):
    def __init__(self, channel: disnake.VoiceChannel):
        self.channel = channel
        options = [
            disnake.SelectOption(label="US Central", value="us-central", emoji="🇺🇸"),
            disnake.SelectOption(label="US East", value="us-east", emoji="🇺🇸"),
            disnake.SelectOption(label="US South", value="us-south", emoji="🇺🇸"),
            disnake.SelectOption(label="US West", value="us-west", emoji="🇺🇸"),
            disnake.SelectOption(label="Brazil", value="brazil", emoji="🇧🇷"),
            disnake.SelectOption(label="Hong Kong", value="hongkong", emoji="🇭🇰"),
            disnake.SelectOption(label="India", value="india", emoji="🇮🇳"),
            disnake.SelectOption(label="Japan", value="japan", emoji="🇯🇵"),
            disnake.SelectOption(label="Rotterdam", value="rotterdam", emoji="🇳🇱"),
            disnake.SelectOption(label="Russia", value="russia", emoji="🏳️"),
            disnake.SelectOption(label="Singapore", value="singapore", emoji="🇸🇬"),
            disnake.SelectOption(label="South Korea", value="south-korea", emoji="🇰🇷"),
            disnake.SelectOption(label="South Africa", value="southafrica", emoji="🇿🇦"),
            disnake.SelectOption(label="Sydney", value="sydney", emoji="🇦🇺"),
        ]
        super().__init__(
            placeholder="Choose a region",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="region",
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        region = self.values[0]
        try:
            await self.channel.edit(rtc_region=region)
        except disnake.HTTPException as e:
            await inter.followup.send(f"❌ | Failed to set region: {e}", ephemeral=True)
            return
        await inter.delete_original_response()


class SetOwnerSelect(disnake.ui.UserSelect):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: VoiceRoomsRepository,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel
        super().__init__(
            placeholder="Choose a user", min_values=1, max_values=1, custom_id="owner"
        )

    async def callback(self, inter: disnake.MessageInteraction):
        new_owner = self.values[0]

        if not new_owner.bot:
            main_room = await self.voices.get_private_room(guild_id=inter.guild_id)
            room: Optional[VoiceRoom] = await self.voices.get_room(main_room, self.channel.id)

            if room and room.owner_id != new_owner:
                embed = custom_embed(
                    title="Transfer Ownership",
                    description=f"Ownership successfully transferred to: {new_owner}",
                )
                await inter.channel.send(embed=embed)
                await self.voices.update_room(main_room, room.id, new_owner.id, room.message)
                return

        elif new_owner.id == inter.author.id:
            embed = custom_embed(
                title="Transfer Ownership",
                description="You cannot transfer the room to yourself.",
            )
            return await inter.channel.send(embed=embed)

        elif new_owner.bot:
            embed = custom_embed(
                title="Transfer Ownership",
                description="You cannot transfer the room to a bot.",
            )
            return await inter.channel.send(embed=embed)


class AccessToChannelSelect(disnake.ui.UserSelect):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: VoiceRoomsRepository,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel
        super().__init__(
            placeholder="Choose user(s)",
            min_values=1,
            max_values=25,
            custom_id="access_to_channel",
        )

    async def callback(self, inter: disnake.MessageInteraction):
        if selected_users := self.values:
            main_room = await self.voices.get_private_room(guild_id=inter.guild_id)
            room: Optional[VoiceRoom] = await self.voices.get_room(main_room, self.channel.id)
            if room:
                for user in selected_users:
                    if perms := self.channel.permissions_for(user):
                        await inter.channel.set_permissions(
                            user, connect=not perms.connect
                        )

                    embed = custom_embed(
                        title="Participant Permissions",
                        description=f"Access to the room has been {'granted' if not perms.connect else 'revoked'} for: **{user.mention}**",
                    )

                    return await inter.send(embed=embed, ephemeral=True)


class MuteUnmuteSelect(disnake.ui.Select):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: VoiceRoomsRepository,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel

        options = []

        for member in channel.members:
            options.append(
                disnake.SelectOption(
                    label=member.name,
                    value=str(member.id),
                    emoji=(
                        "<:unmute:1169690521472614500>"
                        if not member.voice.mute
                        else "<:mute:1170712518725992529>"
                    ),
                )
            )

        super().__init__(
            placeholder="Select participant(s)",
            min_values=1,
            max_values=len(channel.members),
            options=options,
            custom_id="mute_unmute",
        )

    async def callback(self, inter: disnake.MessageInteraction):
        main_room = await self.voices.get_private_room(guild_id=self.channel.id)
        room: Optional[VoiceRoom] = await self.voices.get_room(main_room, self.channel.id)
        if room:
            for member_id in self.values:
                member = inter.guild.get_member(int(member_id))

                await member.edit(
                    voice_channel=self.channel,
                    mute=not member.voice.mute,
                )

                mute_unmute = "Unmute" if not member.voice.mute else "Mute"
                embed = custom_embed(
                    title=f"{mute_unmute} Participant",
                    description=f"Successfully {mute_unmute.lower()}d: **{member.mention}**",
                )
                await inter.send(embed=embed, ephemeral=True)
