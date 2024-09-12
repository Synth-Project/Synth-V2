from tortoise import Model, fields


class UserModel(Model):
    id = fields.BigIntField(primary_key=True)
    songs = fields.ManyToManyField("models.Song", related_name="songs")

    class Meta:
        table = "user"
        table_description = "User model"
