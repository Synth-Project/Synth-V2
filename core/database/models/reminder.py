from tortoise import Model, fields
from enum import Enum


class ReminderType(Enum):
    DM = "DM"
    CHANNEL = "CHANNEL"


class Remind(Model):
    channel_id = fields.BigIntField()
    text = fields.CharField(max_length=256)
    time = fields.IntField()
    type = fields.CharEnumField(ReminderType)

    class Meta:
        table = "reminds"
        table_description = "Remind Model"
