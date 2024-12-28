import disnake
from disnake.ext import commands, tasks
from typing import Optional

from core.database.models.voicerooms import MainRoom
from core.database.repositories import VoiceRoomsRepository

from core.misc.views.voicerooms.buttons import Buttons
from core.misc.embed import custom_embed


class VoiceRooms(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(VoiceRooms, self).__init__()
        self.bot = bot
        self.voices: VoiceRoomsRepository = VoiceRoomsRepository()

    @tasks.loop(seconds=5)
    async def update_rooms(self):
        await self.voices.update_rooms(self.bot)

    # @commands.Cog.listener()
    # async def on_message(self, message: disnake.Message) -> None:
    #     if message.guild:
    #         result: MainRoom = await self.voices.get_private_room(message.guild.id)

    #         # TODO: add option to enable/disable messages in private rooms

    #         if result and message.author.id != self.bot.user.id:
    #             room = await self.voices.get_room(result, channel_id=message.channel.id)
    #             if room and room.owner_id != message.author.id:
    #                 await message.delete()
    #         return

    async def cog_load(self):
        self.update_rooms.start()
        self.bot.add_view(Buttons(bot=self.bot, author=None, channel=None, message=None))

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState,
    ):
        if after.channel and len(after.channel.members) != 0:
            main_room = await self.voices.get_private_room(after.channel.guild.id)

            if main_room and after.channel.id == main_room.channel_id:
                channel = await member.guild.create_voice_channel(
                    name=f"{member.name}'s Room",
                    category=after.channel.category,
                )

                await member.move_to(channel=channel)
                await self.voices.send_room_message(
                    self.bot, channel, member, main_room
                )

        elif before.channel and len(before.channel.members) == 0:
            main_room: Optional[MainRoom] = await self.voices.get_private_room(
                before.channel.guild.id
            )

            if not main_room:
                return

            room = await self.voices.get_room(main_room, before.channel.id)
            if room:
                await before.channel.delete()
                await self.voices.remove_room(main_room, before.channel.id)

        elif member.voice:
            if after.channel != before.channel and member.voice.mute:
                await member.edit(mute=False)

        if before.channel and after.channel and before.channel != after.channel:
            main_room: MainRoom = await self.voices.get_private_room(
                after.channel.guild.id
            )
            if not main_room:
                return

            if len(before.channel.members) == 0:
                room = await self.voices.get_room(main_room, before.channel.id)
                if room:
                    await before.channel.delete()
                    await room.delete()

    @commands.slash_command(name="setup-voice")
    async def setup_voice(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer()
        embed = custom_embed(title="Voice Channel Setup")

        result: MainRoom = await self.voices.get_private_room(
            guild_id=interaction.guild_id
        )
        if result:
            channel = interaction.guild.get_channel(result.channel_id)
            if channel:
                embed.description = (
                    f"Private room already exists. Channel: {channel.mention}"
                )
                await interaction.send(embed=embed)
                return
            else:
                await self.voices.delete_private_room(guild_id=interaction.guild_id)

        voice = await interaction.guild.create_voice_channel(
            name="Create Room", reason="Private room setup"
        )
        await self.voices.create_private_room(
            guild_id=interaction.guild_id, channel_id=voice.id
        )

        embed.description = (
            f"Private room successfully created. Channel: {voice.mention}"
        )
        await interaction.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(VoiceRooms(bot))
