from tortoise import fields, Model


class UserMusic(Model):
    name = fields.CharField(max_length=256)
    url = fields.CharField(max_length=512)
    # dj_role = fields.IntField(default=0, null=True)

    class Meta:
        table = "musics"
        table_description = "Musics Model"

    def __str__(self) -> str:
        return f"Music: name={self.name}, url={self.url}"
