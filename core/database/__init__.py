from tortoise import Tortoise
from core.main.config import settings


async def init_database():
    print("# Initializing database...")
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["core.database.models.base"]},
    )
    await Tortoise.generate_schemas()
    print("# Database initialized!")


async def close_database():
    await Tortoise.close_connections()