from tortoise import Model, fields


class UserModel(Model):
    id = fields.BigIntField(primary_key=True)
    musics = fields.ManyToManyField("models.Music", related_name="musics")

    class Meta:
        table = "user"
        table_description = "User model"
