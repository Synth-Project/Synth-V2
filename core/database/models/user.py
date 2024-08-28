from tortoise import Model, fields


class UserModel(Model):
    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()

    class Meta:
        table = "user"
        table_description = "User model"
        abstract = True
