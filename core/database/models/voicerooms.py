from tortoise import fields
from tortoise.models import Model
from core.database.models.base import BaseModel


class VoiceRoom(Model):
    id = fields.BigIntField(primary_key=True)
    owner_id = fields.BigIntField()
    message = fields.BigIntField(null=True)

    class Meta:
        table = "voice_rooms"
        table_description = "Voice rooms"

    def __str__(self) -> str:
        return (
            f"VoiceRoom: id={self.id}, owner_id={self.owner_id}, message={self.message}"
        )


class MainRoom(BaseModel):
    channel_id = fields.BigIntField()
    rooms = fields.ManyToManyField("models.VoiceRoom", related_name="rooms")

    class Meta:
        table = "main_rooms"
        table_description = "Main rooms"

    def __str__(self) -> str:
        return f"MainRoom in guild {self.guild_id} on channel {self.channel_id}"
