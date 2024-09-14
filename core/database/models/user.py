from tortoise import Model, fields


class UserModel(Model):
    id = fields.BigIntField(primary_key=True)
    reminds = fields.ManyToManyField("models.Remind", related_name="reminds")
    birthday = fields.OneToOneField(
        "models.BirthdayModel", related_name="birthday", null=True
    )

    class Meta:
        table = "user"
        table_description = "User model"


class BirthdayModel(Model):
    day = fields.IntField()
    month = fields.IntField()

    class Meta:
        table = "birthday"
        table_description = "Birthday model"
