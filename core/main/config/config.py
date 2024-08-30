from typing import List

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DEBUG: bool
    BOT_TOKEN: str
    OWNERS: List[int]
    TEST_GUILDS: List[int]

    @property
    def DATABASE_URL(self) -> str:
        # return "sqlite://synthdb.sqlite3"  # FOR LOCAL ONLY
        return "postgres://synth:SyNTh@@1337@!@146.148.127.63:5432/synth"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
    )


settings = Settings()
