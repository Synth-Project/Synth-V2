from typing import List

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DEBUG: bool
    BOT_TOKEN: str
    OWNERS: List[int]
    TEST_GUILDS: List[int]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
    )


settings = Settings()
