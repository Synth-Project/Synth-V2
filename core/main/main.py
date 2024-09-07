from core.main.config.config import settings
from core.bot import Bot

bot = Bot()

if __name__ == "__main__":
    bot.run(settings.BOT_TOKEN)
