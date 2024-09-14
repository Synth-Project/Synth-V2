import os
import sys
import asyncio
import importlib
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.bot import Bot
from core.main.config.config import settings

bot = Bot()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AsyncFileChangeHandler(FileSystemEventHandler):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        base_path: str,
        debounce_time: float = 1.0,
    ):
        self.loop = loop
        self.base_path = base_path
        self.debounce_time = debounce_time
        self.last_modified = {}

    def on_modified(self, event):
        if event.src_path.endswith(".py") and not any(
            part in event.src_path for part in ["__pycache__", ".pyc"]
        ):
            current_time = time.monotonic()
            last_time = self.last_modified.get(event.src_path, 0)
            if current_time - last_time > self.debounce_time:
                settings.DEBUG and print(f"Changed file: {event.src_path}")
                self.last_modified[event.src_path] = current_time
                asyncio.run_coroutine_threadsafe(
                    self._reload_module(event.src_path), self.loop
                )

    async def _reload_module(self, file_path: str):
        try:
            module_name = f"core.{os.path.relpath(file_path, self.base_path).replace(os.path.sep, '.')}".rstrip(
                ".py"
            )
            importlib.invalidate_caches()
            self._reload_core_modules()
            settings.DEBUG and print(f"Reloaded: {module_name}")
        except BaseException as error:
            settings.DEBUG and print(f"Error reloading module: {error}")

        from core.database import init_database, close_database

        await close_database()

        await init_database()

    @staticmethod
    def _reload_core_modules():
        for name, module in list(sys.modules.items()):
            if name.startswith("core.") and not "__pycache__" in name:
                try:
                    importlib.reload(module)
                    # settings.DEBUG and print(f"Reloaded: {name}")
                except BaseException as error:
                    settings.DEBUG and print(f"Error reloading {name}: {error}")


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
    loop.create_task(start_watching(loop, os.path.join(os.getcwd(), "core")))
    loop.run_until_complete(bot.run(settings.BOT_TOKEN))
