from tortoise import Model, fields

class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "base"
        table_description = "Base model"
        abstract = Trueя

class TestModel(BaseModel):
    name = fields.CharField(max_length=255)

    class Meta:
        table = "test"
        table_description = "Test model"
    
    def __str__(self) -> str:
        return super().__str__()