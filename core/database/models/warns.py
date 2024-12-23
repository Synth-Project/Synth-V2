from tortoise import fields, Model


class WarnsModel(Model):
    id = fields.BigIntField(pk=True)
    warn_id = fields.BigIntField(default=0)

    user = fields.ForeignKeyField("models.UserModel", related_name="user")
    warned_by = fields.BigIntField()
    reason = fields.TextField(null=True)

    date = fields.DatetimeField(auto_now_add=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    remove_at = fields.DatetimeField(null=True)

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
