from tortoise import fields, Model


class WarnsModel(Model):
    id = fields.BigIntField(pk=True)
    # user_id = fields.()
    user = fields.ForeignKeyField("models.UserModel", related_name="user")
    # guild_id = fields.BigIntField()
    warned_by = fields.BigIntField()
    date = fields.DatetimeField(auto_now_add=True)
    warn_id = fields.BigIntField(default=0)
    reason = fields.TextField(null=True)
    remove_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    async def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        if self.warn_id is None:
            last_warn = (
                await WarnsModel.filter(user=self.user).order_by("-warn_id").first()
            )
            self.warn_id = last_warn.warn_id + 1 if last_warn else 1

        return await super().save(*args, **kwargs)

    class Meta:
        table = "warns"
        table_description = "Warns model"
        # unique_together = ("user", "warn_id")
