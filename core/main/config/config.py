import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DEBUG: bool
    BOT_TOKEN: str
    OWNERS: list[int]
    TEST_GUILDS: list[int]

    @property
    def DATABASE_URL(self) -> str:
        return "sqlite://synthdb.sqlite3"  # Local DB
        # return "postgres://synth:SyNTh@@1337@!@nixxoq.xyz:5432/synth"

    model_config = SettingsConfigDict(  # type: ignore
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
    )


settings = Settings()  # type: ignore[reportCallIssue]
