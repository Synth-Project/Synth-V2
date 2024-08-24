from tortoise import Model, fields


class BaseModel(Model):
    id = fields.IntField(pk=True)

    class Meta:
        table = "base"
        table_description = "Base model"
        abstract = True


class TestModel(BaseModel):
    name = fields.CharField(max_length=255)

    class Meta:
        table = "test"
        table_description = "Test model"

    def __str__(self) -> str:
        return super().__str__()
