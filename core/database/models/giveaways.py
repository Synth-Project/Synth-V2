from tortoise import fields, Model
# from tortoise.contrib.postgres.fields import ArrayField

class GiveawayModel(Model):
    prize = fields.CharField(max_length=32)
    winners = fields.BigIntField()
    end_time = fields.BigIntField()
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField(primary_key=True)
    ended = fields.BooleanField()
    members = fields.JSONField(default=[])

    class Meta:
        table = "giveaways"
        table_description = "Just giveaway model"

    def __str__(self) -> str:
        return f"GiveawayModel: prize={self.prize}, winners={self.winners}, end_time={self.end_time}, channel_id={self.channel_id}, message_id={self.message_id}, ended={self.ended}, members={self.members}"