from tortoise import fields, Model
from enum import Enum


# from tortoise.contrib.postgres.fields import ArrayField

class VoiceEnum(Enum):
    ANY_VC = "any_vc"
    ANY_SG = "any_sg"
    SPECIFIED_SG = "specified_sg"
    SPECIFIED_VC = "specified_vc"
    SPECIFIED_CG = "category"

class GiveawayModel(Model):
    prize = fields.CharField(max_length=32)
    winners = fields.BigIntField()
    end_time = fields.BigIntField()
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField(primary_key=True)
    ended = fields.BooleanField()
    members = fields.JSONField(default=[])
    voice = fields.CharEnumField(enum_type=VoiceEnum, null=False)
    voice_id = fields.BigIntField()

    class Meta:
        table = "giveaways"
        table_description = "Just giveaway model"

    def __str__(self) -> str:
        return f"GiveawayModel: prize={self.prize}, winners={self.winners}, end_time={self.end_time}, channel_id={self.channel_id}, message_id={self.message_id}, ended={self.ended}, members={self.members}, voice={self.voice}, voice_id={self.voice_id}"