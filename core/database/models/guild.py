from tortoise import fields, Model


class GuildModel(Model):
    id = fields.BigIntField(primary_key=True)
    music_settings: fields.JSONField[dict[str, any]] = fields.JSONField(default=dict)

    class Meta:
        table = "guild"
        table_description = "Guild model"

    def __str__(self) -> str:
        return f"Guild: music_settings={self.music_settings}"
