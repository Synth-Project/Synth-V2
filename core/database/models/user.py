from tortoise import Model, fields
from core.database.models.warns import WarnsModel


class UserModel(Model):
    id = fields.BigIntField(primary_key=True)
    # musics = fields.ManyToManyField("models.UserMusic", related_name="musics")
    warns = fields.ReverseRelation["WarnsModel"]

    class Meta:  # type: ignore
        table = "user"
        table_description = "User model"
