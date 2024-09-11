from tortoise import Model, fields


class UserModel(Model):
    id = fields.BigIntField(primary_key=True)
    reminds = fields.ManyToManyField("models.Remind", related_name="reminds")

    class Meta:
        table = "user"
        table_description = "User model"
