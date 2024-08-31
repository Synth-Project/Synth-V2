from tortoise import Model, fields


class BaseModel(Model):
    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()

    class Meta:
        abstract = True
