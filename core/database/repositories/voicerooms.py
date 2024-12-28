import disnake
from core.database.models import VoiceRoom, MainRoom
from core.database.repositories.base import BaseRepository
from typing import Optional
from disnake.ext import commands
from core.misc.util.misc import get_message, get_channel
from core.misc.embed import custom_embed


class VoiceRoomsRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    async def get_one(**kwargs) -> MainRoom | None:
        return await MainRoom.filter(**kwargs).first().prefetch_related("rooms")

    @staticmethod
    async def get_all(**kwargs) -> list[MainRoom]:
        return await MainRoom.filter(**kwargs).all().prefetch_related("rooms")

    @staticmethod
    async def add_one(**kwargs) -> tuple[MainRoom, bool]:
        return await MainRoom.get_or_create(**kwargs)

    @staticmethod
    async def remove_one(**kwargs):
        return await MainRoom.filter(**kwargs).delete()

    async def create_private_room(self, guild_id: int, channel_id: int) -> MainRoom:
        main_room, _ = await self.add_one(guild_id=guild_id, channel_id=channel_id)

        return main_room

    async def get_private_room(self, guild_id: int) -> Optional[MainRoom]:
        result: Optional[MainRoom] = await self.get_one(guild_id=guild_id)
        if not result:
            return None

        return result

    async def delete_private_room(self, guild_id: int) -> None:
        await self.remove_one(guild_id=guild_id)

    async def add_room(
        self, main_room: MainRoom, channel_id: int, owner_id: int, message_id: int
    ) -> None:
        if await self.get_room(main_room, channel_id):
            await self.update_room(main_room, channel_id, owner_id, message_id)
            return
        voice_room = await VoiceRoom.create(
            id=channel_id, owner_id=owner_id, message=message_id
        )
        await main_room.rooms.add(voice_room)
    
    async def update_room(
        self, main_room: MainRoom, channel_id: int, owner_id: int, message_id: int
    ):
        await self.remove_room(main_room, channel_id)
        await self.add_room(main_room, channel_id, owner_id, message_id)

    async def get_room(
        self, main_room: MainRoom, channel_id: int
    ) -> Optional[VoiceRoom]:
        result: Optional[VoiceRoom] = await main_room.rooms.filter(
            id=channel_id
        ).first()
        if not result:
            return None

        return result

    async def remove_room(self, main_room: MainRoom, channel_id: int) -> None:
        result: Optional[VoiceRoom] = await self.get_room(main_room, channel_id)
        if not result:
            return None

        await result.delete()

    async def update_rooms(self, bot: commands.Bot) -> None:
        for main_room in await self.get_all():
            for room in await main_room.rooms.all():
                room: VoiceRoom = room
                channel: Optional[disnake.VoiceChannel] = await get_channel(bot, room.id)
                if not channel:
                    await self.remove_room(main_room, room.id)
                elif len(channel.members) == 0:
                    await channel.delete()
                    await self.remove_room(main_room, room.id)
                else:
                    message = await get_message(bot, room.message, channel)
                    if message:
                        await self.update_embed(channel, message, main_room)
                    else:
                        owner = await channel.guild.get_or_fetch_member(room.owner_id)
                        await self.send_room_message(bot, channel, owner, main_room)

    async def update_embed(
        self,
        channel: disnake.VoiceChannel,
        message: disnake.Message,
        main_room: MainRoom,
    ):
        room: Optional[VoiceRoom] = await self.get_room(main_room, channel.id)
        if not room:
            return

        owner = await channel.guild.get_or_fetch_member(room.owner_id)
        text = (
            f"- **Owner:** {owner.mention if owner else 'Unknown'}\n"
            f"- **Limit:** {channel.user_limit or '∅'}\n"
            f"- **Members:** {len(channel.members)}\n"
            f"- **Bitrate:** {channel.bitrate // 1000} kbps\n"
            f"- **Region:** {channel.rtc_region.capitalize() if channel.rtc_region else 'Automatic'}\n"
            f"- **Locked:** {"✅" if not channel.permissions_for(channel.guild.default_role).connect else "❌"}\n"
        )
        if message.embeds[0]:
            embed = message.embeds[0]
            if embed.fields:
                embed.set_field_at(0, name="Room Settings", value=text)
            else:
                embed.add_field(name="Room Settings", value=text)

        await message.edit(embed=embed, content = owner.mention if owner else None)

    async def send_room_message(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        member: disnake.Member,
        main_room: MainRoom,
    ):
        from core.misc.views.voicerooms.buttons import Buttons
        embed = custom_embed(title="Private Room Settings")
        embed.description = (
            "<:store:1169690541986959464> - Change channel name\n"
            "<:members:1169684583369949285> - Change room limit\n"
            "<:list:1169690529643114547> - Remove room limit\n"
            "<:invite:1169690514430382160> - Lock/Unlock room for everyone\n"
            "<:ban:1170712517308317756> - Kick a member from the room\n"
            "<:hammer:1169685339720384512> - Grant/Remove access to the room\n"
            "<:mute:1170712518725992529> - Mute/Unmute a member in the room\n"
            "<:owner:1169684595697004616> - Transfer room ownership\n"
            "📝 - Enable/Disable message permissions in the room\n"
            "🌐 - Change room region\n"
            "🔊 - Change room bitrate\n"
        )
        message = await channel.send(
            content=member.mention,
            embed=embed,
        )
        await self.add_room(main_room, channel.id, member.id, message.id)
        await message.edit(
            view=Buttons(
                bot=bot,
                author=member,
                channel=channel,
                message=message,
            ),
        )
        await self.update_embed(channel, message, main_room)
