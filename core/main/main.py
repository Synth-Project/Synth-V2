from core.main.config.config import settings
from core import bot

if __name__ == "__main__":
    try:
        bot.Bot().run(settings.BOT_TOKEN)
    except BaseException:
        import traceback

        traceback.print_exc()
