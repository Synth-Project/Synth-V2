from tortoise import Tortoise

from core.main.config import settings
from core import logger


async def init_database():
    settings.DEBUG and logger.info("# Initializing database...")
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["core.database.models.__init__"]},
    )
    await Tortoise.generate_schemas()
    settings.DEBUG and logger.info("# Database initialized")



async def close_database():
    await Tortoise.close_connections()
