import disnake
from disnake.ext import commands

from core.database.models.voicerooms import MainRoom, VoiceRoom

from core.misc.views.voicerooms.other import (
    BitrateSelect,
    SetChannelName,
    SetUserLimit,
    KickUsersSelect,
    RegionSelect,
    SetOwnerSelect,
    AccessToChannelSelect,
    MuteUnmuteSelect,
)
from core.misc.embed import custom_embed
from typing import Optional


class Buttons(disnake.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        author: disnake.Member,
        channel: disnake.VoiceChannel,
        voices: MainRoom,
        message: disnake.Message,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.author = author
        self.voices = voices
        self.channel = channel
        self.message = message

    @disnake.ui.button(emoji="<:store:1169690541986959464>", custom_id="pen", row=0)
    async def pen_callback(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        modal = SetChannelName(bot=self.bot, channel=self.channel)
        await interaction.response.send_modal(modal)

    @disnake.ui.button(emoji="<:members:1169684583369949285>", row=0, custom_id="users")
    async def _users(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        modal = SetUserLimit(bot=self.bot, channel=self.channel)
        await interaction.response.send_modal(modal)

    @disnake.ui.button(emoji="<:list:1169690529643114547>", row=0, custom_id="unlock")
    async def _unlock_slot(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        await self.channel.edit(user_limit=0)
        embed = custom_embed(
            title="Participant Limit",
            description="Limit successfully removed.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @disnake.ui.button(emoji="<:invite:1169690514430382160>", row=0, custom_id="lock")
    async def _lock_unlock(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer(ephemeral=True)
        if perms := self.channel.permissions_for(interaction.guild.default_role):
            main_room = await self.voices.get_or_none(guild_id=interaction.guild_id)
            room = await main_room.rooms.filter(id=self.channel.id).first()
            owner = interaction.guild.get_member(room.owner_id)
            await self.channel.set_permissions(owner, connect=True)

            await self.channel.set_permissions(
                interaction.guild.default_role, connect=not perms.connect
            )

    @disnake.ui.button(emoji="<:ban:1170712517308317756>", row=1, custom_id="kick")
    async def _kick(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()

        view.add_item(
            KickUsersSelect(self.bot, channel=self.channel, voices=self.voices)
        )

        embed = custom_embed(
            title="Kick Participants",
            description="Select participants to kick from your private room",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(emoji="<:hammer:1169685339720384512>", row=1, custom_id="access")
    async def _access(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()

        view.add_item(
            AccessToChannelSelect(self.bot, channel=self.channel, voices=self.voices)
        )

        embed = custom_embed(
            title="Access to Channel",
            description="Select participants to give access to your private room",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(emoji="<:mute:1170712518725992529>", row=1, custom_id="mute")
    async def _mute(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()
        view.add_item(
            MuteUnmuteSelect(self.bot, channel=self.channel, voices=self.voices)
        )

        embed = custom_embed(
            title="Mute/Unmute Participants",
            description="Select participants to mute/unmute in your private room",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(
        emoji="<:owner:1169684595697004616>", row=1, custom_id="transfer"
    )
    async def transfer_ownership(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()

        view.add_item(
            SetOwnerSelect(self.bot, channel=self.channel, voices=self.voices)
        )

        embed = custom_embed(
            title="Transfer Room Ownership",
            description="Transfer ownership of a private room to another user",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(emoji="📝", row=2, custom_id="chat")
    async def toggle_chat(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        current_perms = self.channel.permissions_for(
            interaction.guild.default_role
        ).send_messages

        embed = custom_embed(
            title="Toggle Chat",
            description=f"Successfully {'enabled' if current_perms else 'disabled'} chat in the room",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        main_room = await self.voices.get_or_none(guild_id=interaction.guild_id)
        room: VoiceRoom = await main_room.rooms.filter(id=self.channel.id).first()
        owner = interaction.guild.get_member(room.owner_id)
        await self.channel.set_permissions(
            interaction.guild.default_role, send_messages=not current_perms
        )
        await self.channel.set_permissions(owner, send_messages=True)

    @disnake.ui.button(emoji="🌐", row=2, custom_id="region")
    async def change_region(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()
        view.add_item(RegionSelect(self.channel))
        embed = custom_embed(
            title="Change Region",
            description="Select a region for the voice channel from the dropdown below.",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(emoji="🎧", row=2, custom_id="bitrate")
    async def change_bitrate(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()
        view.add_item(BitrateSelect(self.channel))
        embed = custom_embed(
            title="Change Bitrate",
            description="Select a bitrate for the voice channel from the dropdown below.",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if not self.message or not self.voices or not self.channel or not self.author:
            await interaction.response.send_message(
                "❌ | Something went wrong. Try to recreate the room.", ephemeral=True
            )
            return False
        result = await self.voices.get_or_none(guild_id=interaction.guild_id)
        if result:
            room: Optional[VoiceRoom] = await result.rooms.filter(
                id=self.channel.id
            ).first()

            if room and room.owner_id != interaction.author.id:
                embed = custom_embed(
                    description="<a:error:1168599839899144253> You do not have permission to use these buttons",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
            return True
        return False
