from tortoise import fields, Model

from core.database.models.user import UserModel


class Song(Model):
    name = fields.CharField(max_length=100)
    url = fields.CharField(max_length=256)

    class Meta:
        table = "songs"
        table_description = "Song Model"

    def __str__(self) -> str:
        return f"Song: name={self.name}, url={self.url}"


class MusicModel(UserModel):
    id = fields.BigIntField(primary_key=True)
    songs = fields.ManyToManyField("models.Song", related_name="music")

    class Meta:
        table = "music"
        table_description = "Music Model"

    def __str__(self) -> str:
        return f"MusicModel: id={self.id}, user_id={self.user_id}"
