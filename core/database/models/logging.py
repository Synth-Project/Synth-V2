from tortoise import fields, Model
from core.database.models.base import BaseModel


class Logging(BaseModel):
    message_logs = fields.OneToOneField(
        "models.MessageLogging", related_name="message_logs", through="message_logs"
    )
    member_logs = fields.OneToOneField(
        "models.MemberLogging", related_name="member_logs", through="member_logs"
    )
    reaction_logs = fields.OneToOneField(
        "models.ReactionLogging", related_name="reaction_logs", through="reaction_logs"
    )
    guild_logs = fields.OneToOneField(
        "models.GuildLogging", related_name="guild_logs", through="guild_logs"
    )
    channel_logs = fields.OneToOneField(
        "models.ChannelLogging", related_name="channel_logs", through="channel_logs"
    )
    role_logs = fields.OneToOneField(
        "models.RoleLogging", related_name="role_logs", through="role_logs"
    )

    class Meta:
        table = "logs"
        table_description = "Log Model"


class MemberLogging(Model):
    join_event = fields.BooleanField(default=False)
    join_event_channel_id = fields.BigIntField(default=0)

    leave_event = fields.BooleanField(default=False)
    leave_event_channel_id = fields.BigIntField(default=0)

    ban_event = fields.BooleanField(default=False)
    ban_event_channel_id = fields.BigIntField(default=0)

    unban_event = fields.BooleanField(default=False)
    unban_event_channel_id = fields.BigIntField(default=0)

    update_event = fields.BooleanField(default=False)
    update_event_channel_id = fields.BigIntField(default=0)

    class Meta:
        table = "member_logs"
        table_description = "Member Log Model"


class MessageLogging(Model):
    delete_event = fields.BooleanField(default=False)
    delete_event_channel_id = fields.BigIntField(default=0)

    edit_event = fields.BooleanField(default=False)
    edit_event_channel_id = fields.BigIntField(default=0)

    class Meta:
        table = "message_logs"
        table_description = "Message Log Model"


class ReactionLogging(Model):
    add_event = fields.BooleanField(default=False)
    add_event_channel_id = fields.BigIntField(default=0)

    remove_event = fields.BooleanField(default=False)
    remove_event_channel_id = fields.BigIntField(default=0)

    clear_event = fields.BooleanField(default=False)
    clear_event_channel_id = fields.BigIntField(default=0)

    class Meta:
        table = "reaction_logs"
        table_description = "Reaction Log Model"


class GuildLogging(Model):
    update_event = fields.BooleanField(default=False)
    update_event_channel_id = fields.BigIntField(default=0)

    class Meta:
        table = "guild_logs"
        table_description = "Guild Log Model"


class ChannelLogging(Model):
    create_event = fields.BooleanField(default=False)
    create_event_channel_id = fields.BigIntField(default=0)

    update_event = fields.BooleanField(default=False)
    update_event_channel_id = fields.BigIntField(default=0)

    delete_event = fields.BooleanField(default=False)
    delete_event_channel_id = fields.BigIntField(default=0)

    class Meta:
        table = "channel_logs"
        table_description = "Channel Log Model"


class RoleLogging(Model):
    create_event = fields.BooleanField(default=False)
    create_event_channel_id = fields.BigIntField(default=0)

    update_event = fields.BooleanField(default=False)
    update_event_channel_id = fields.BigIntField(default=0)

    delete_event = fields.BooleanField(default=False)
    delete_event_channel_id = fields.BigIntField(default=0)

    class Meta:
        table = "role_logs"
        table_description = "Role Log Model"
