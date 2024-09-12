from tortoise import fields, Model


class Song(Model):
    name = fields.CharField(max_length=100)
    url = fields.CharField(max_length=256)

    class Meta:
        table = "songs"
        table_description = "Song Model"

    def __str__(self) -> str:
        return f"Song: name={self.name}, url={self.url}"
