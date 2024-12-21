from tortoise import Model, fields


class UserModel(Model):
    id = fields.BigIntField(primary_key=True)
    # musics = fields.ManyToManyField("models.UserMusic", related_name="musics")
    warns = fields.ReverseRelation["WarnsModel"]

    class Meta:  # type: ignore
        table = "user"
        table_description = "User model"
