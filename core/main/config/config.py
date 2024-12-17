import os
from typing import List

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool
    BOT_TOKEN: SecretStr
    OWNERS: List[int]
    TEST_GUILDS: List[int]
    BOT_LOGS_ID: int

    @property
    def DATABASE_URL(self) -> str:
        return "sqlite://synthdb.sqlite3"  # FOR LOCAL ONLY
        # return "postgres://synth:SyNTh@@1337@!@146.148.127.63:5432/synth"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
    )


settings = Settings()
