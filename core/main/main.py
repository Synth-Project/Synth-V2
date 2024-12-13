import asyncio
import importlib
import os
import sys

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.bot import Bot
from core.main.config.config import settings

bot = Bot()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AsyncFileChangeHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, base_path: str):
        self.loop = loop
        self.base_path = base_path

    def on_modified(self, event):
        if event.src_path.endswith(".py") and not any(  # type: ignore
            part in event.src_path for part in ["__pycache__", ".pyc"]  # type: ignore
        ):
            settings.DEBUG and print(f"Changed file: {event.src_path}")  # type: ignore
            asyncio.run_coroutine_threadsafe(
                self._reload_module(event.src_path), self.loop  # type: ignore
            )

    async def _reload_module(self, file_path: str):
        try:
            module_name = f"core.{os.path.relpath(file_path, self.base_path).replace(os.path.sep, '.')}".rstrip(
                ".py"
            )
            importlib.invalidate_caches()
            self._reload_core_modules()
            settings.DEBUG and print(f"Reloaded: {module_name}")  # type: ignore
        except BaseException as error:
            settings.DEBUG and print(f"Error reloading module: {error}")  # type: ignore

        from core.database import init_database

        await init_database()

    @staticmethod
    def _reload_core_modules():
        for name, module in list(sys.modules.items()):
            if name.startswith("core.") and not "__pycache__" in name:
                try:
                    importlib.reload(module)
                    settings.DEBUG and print(f"Reloaded: {name}")  # type: ignore
                except BaseException as error:
                    settings.DEBUG and print(f"Error reloading {name}: {error}")  # type: ignore


async def start_watching(loop: asyncio.AbstractEventLoop, path: str):
    if settings.DEBUG and not os.path.exists(path):
        print(f"Error: Path {path} does not exist.")
        return

    observer = Observer()
    observer.schedule(AsyncFileChangeHandler(loop, path), path=path, recursive=True)
    observer.start()

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    #! Watchdogs doesn't work correctly now
    # loop.create_task(start_watching(loop, os.path.join(os.getcwd(), "core")))
    loop.run_until_complete(bot.run(settings.BOT_TOKEN))  # type: ignore
