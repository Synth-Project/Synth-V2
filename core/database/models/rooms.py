from core.database.models.base import BaseModel

from tortoise import fields
from tortoise.models import Model


class VoiceRoom(Model):
    id = fields.BigIntField(primary_key=True)
    owner_id = fields.BigIntField()

    class Meta:
        table = "rooms"
        table_description = "Voice rooms"

    def __str__(self) -> str:
        return f"VoiceRoom: id={self.id}, owner_id={self.owner_id}"


class MainRoom(BaseModel):
    id = fields.BigIntField(primary_key=True)
    channel_id = fields.BigIntField()
    rooms = fields.ManyToManyField("models.VoiceRoom", related_name="main_rooms", through="voice_rooms")

    class Meta:
        table = "main_rooms"
        table_description = "Main rooms"

    def __str__(self) -> str:
        return f"MainRoom in guild {self.guild_id} on channel {self.channel_id}"
