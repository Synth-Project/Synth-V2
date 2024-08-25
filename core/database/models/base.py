from tortoise import Model, fields


class BaseModel(Model):
    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()

    class Meta:
        table = "base"
        table_description = "Base model"
        abstract = True
