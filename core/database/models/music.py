from core.database.models.user import UserModel

from tortoise import fields
from tortoise.models import Model


class MusicModel(UserModel):
    id = fields.BigIntField(primary_key=True)
    songs = fields.JSONField(default=[])

    class Meta:
        table = "music"
        table_description = "Music"

    def __str__(self) -> str:
        return f"Music: id={self.id}, user_id={self.user_id}, songs={self.songs}"