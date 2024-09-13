# import importlib
# import os
# import sys
#
# from core.main.config.config import settings
# from core.bot import Bot
#
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# import asyncio
#
# bot = Bot()
#
# sys.path.append(os.path.abspath("../../core"))
# sys.path.append(os.path.abspath("../../core/cogs"))
# sys.path.append(os.path.abspath("../../core/database"))
# sys.path.append(os.path.abspath("../../core/misc"))
#
# class AsyncFileChangeHandler(FileSystemEventHandler):
#     def __init__(self, event_loop: asyncio.AbstractEventLoop, path: str):
#         self.loop = event_loop
#         self.base_path = path
#
#     def on_modified(self, event):
#         if event.src_path.endswith(".py"):
#             print(f"Изменен файл: {event.src_path}")
#             # Асинхронно запускаем перезагрузку всех модулей
#             asyncio.run_coroutine_threadsafe(self.async_reload_on_change(), self.loop)
#
#     async def async_reload_on_change(self):
#         try:
#             await self.async_find_and_reload_modules(self.base_path)  # Перезагружаем все модули
#         except Exception as e:
#             print(f"Ошибка при перезагрузке модулей: {e}")
#
#     # @staticmethod
#     # async def async_find_and_reload_modules(base_path: str):
#     #     for root, dirs, files in os.walk(base_path):
#     #         for file in files:
#     #             if file.endswith(".py") and file != "__init__.py":
#     #                 module_path = os.path.join(root, file)
#     #                 module_name = (
#     #                     module_path
#     #                     .replace(base_path, '')
#     #                     .replace('/', '.')
#     #                     .replace('\\', '.')
#     #                     .replace('.py', '')
#     #                 )
#     #                 if module_name.startswith('.'):
#     #                     module_name = module_name[1:]  # Убираем ведущую точку
#     #
#     #                 try:
#     #                     module = importlib.import_module(module_name)
#     #                     importlib.reload(module)
#     #                     print(f"Модуль {module_name} успешно перезагружен!")
#     #                 except Exception as e:
#     #                     print(f"Ошибка при перезагрузке модуля {module_name}: {e}")
#     #
#     #     await asyncio.sleep(0)  # Асинхронная пауза, чтобы избежать блокировки
#
#
#     @staticmethod
#     async def async_find_and_reload_modules(base_path):
#         for root, dirs, files in os.walk(base_path):
#             for file in files:
#                 if file.endswith(".py"):
#                     module_path = os.path.relpath(os.path.join(root, file), base_path)
#                     module_name = module_path.replace(os.path.sep, ".").rstrip(".py")
#
#                     # Перезагрузить модуль
#                     try:
#                         if module_name in sys.modules:
#                             importlib.reload(sys.modules[module_name])
#                             print(f"Перезагружен модуль: {module_name}")
#                         else:
#                             print(f"Модуль не найден: {module_name}")
#                     except Exception as e:
#                         print(f"Ошибка при перезагрузке модуля {module_name}: {e}")
#
# async def start_watching(ev_loop: asyncio.AbstractEventLoop, paths: list[str]):
#     observers = []
#
#
#     for path in paths:
#         if not os.path.exists(path):
#             print(f"Ошибка: Путь {path} не существует.")
#             continue  # Пропустить несуществующие пути
#
#         event_handler = AsyncFileChangeHandler(ev_loop, path)
#         observer = Observer()
#         observer.schedule(event_handler, path=path, recursive=True)  # Отслеживаем все папки
#         observer.start()
#         observers.append(observer)
#
#     try:
#         while True:
#             await asyncio.sleep(1)  # Асинхронный цикл для предотвращения блокировки
#     except KeyboardInterrupt:
#         for observer in observers:
#             observer.stop()
#     for observer in observers:
#         observer.join()
#
#
# if __name__ == "__main__":
#     # bot.run(settings.BOT_TOKEN)
#
#     loop = asyncio.get_event_loop()
#
#     loop.create_task(start_watching(loop, [
#         f"{os.getcwd()}/core",
#         f"{os.getcwd()}/core/cogs",
#         f"{os.getcwd()}/core/database",
#         f"{os.getcwd()}/core/misc",
#     ]))
#
#     loop.run_until_complete(bot.run(settings.BOT_TOKEN))
#
#     bot = Bot()


import asyncio
import importlib
import os
import sys

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.bot import Bot
from core.main.config.config import settings

bot = Bot()
# print("Current working directory:", os.getcwd())
# print("Python path:", sys.path)
# Получаем путь к текущему файлу
current_file = os.path.abspath(__file__)
#
# # Получаем путь к корневому каталогу проекта
project_root = os.path.dirname(os.path.dirname(current_file))
#
# # Добавляем путь к проекту в список путей
sys.path.insert(0, project_root)
print(project_root)

# class AsyncFileChangeHandler(FileSystemEventHandler):
#     def __init__(self, event_loop: asyncio.AbstractEventLoop, path: str):
#         self.loop = event_loop
#         self.base_path = path
#
#     def on_modified(self, event):
#         if event.src_path.endswith(".py"):
#             print(f"Found changed file: {event.src_path}")
#             self.event = event
#             # Асинхронно запускаем перезагрузку модуля
#             asyncio.run_coroutine_threadsafe(self.async_reload_on_change(), self.loop)
#
#     # def on_modified(self, event):
#     #     if event.src_path.endswith(".py"):
#     #         print(f"Изменен файл: {event.src_path}")
#     #         # Асинхронно запускаем перезагрузку всех модулей
#     #         asyncio.run_coroutine_threadsafe(self.async_reload_on_change(), self.loop)
#
#     async def async_reload_on_change(self):
#         try:
#             file_path = self.event.src_path
#             module_name = file_path.replace(self.base_path, '').replace('.py', '').replace('/', '.').replace('\\', '.')
#
#             if module_name.startswith('.'):
#                 module_name = module_name[1:]
#
#             module_name = f"core.{module_name}"
#             print(f"Reloading module: {module_name}")
#             # Перезагружаем модуль и его родительские модули
#             parts = module_name.split('.')
#             for i in range(1, len(parts) + 1):
#                 parent_module_name = '.'.join(parts[:i])
#                 if parent_module_name in sys.modules:
#                     importlib.invalidate_caches()
#                     # sys.modules.pop(parent_module_name, None)
#                     parent_module = importlib.import_module(parent_module_name)
#                     importlib.reload(parent_module)
#                     print(f"Reloaded module: {parent_module_name}")
#         except Exception as e:
#             print(f"Error while reloading module: {e}")
#
#     # async def async_reload_on_change(self):
#     #     try:
#     #         # Получаем путь к измененному файлу
#     #         file_path = self.event.src_path
#     #         # Получаем имя модуля
#     #         module_name = file_path.replace(self.base_path, '').replace('.py', '').replace('/', '.').replace('\\', '.')
#     #         if module_name.startswith('.'):
#     #             module_name = module_name[1:]  # Убираем ведущую точку
#     #
#     #         module_name = f"core.{module_name}"
#     #         # Перезагружаем модуль
#     #         importlib.invalidate_caches()
#     #         # Удаляем модуль из словаря sys.modules
#     #         sys.modules.pop(module_name, None)
#     #         # Перезагружаем модуль
#     #         module = importlib.import_module(module_name)
#     #         importlib.reload(module)
#     #         # print(f"Перезагружен модуль: {module_name}")
#     #         # module = importlib.import_module(module_name)
#     #         # importlib.reload(module)
#     #         print(f"Reloaded module: {module_name}")
#     #     except Exception as e:
#     #         print(f"Error while reloading module: {e}")
#
#     # async def async_reload_on_change(self):
#     #     try:
#     #         await self.async_find_and_reload_modules(self.base_path)  # Перезагружаем все модули
#     #     except Exception as e:
#     #         print(f"Ошибка при перезагрузке модулей: {e}")
#
#     # @staticmethod
#     # async def async_find_and_reload_modules(base_path):
#     #     for root, dirs, files in os.walk(base_path):
#     #         for file in files:
#     #             if file.endswith(".py") and file != "__init__.py":
#     #                 module_path = os.path.relpath(os.path.join(root, file), base_path)
#     #                 module_name = module_path.replace(os.path.sep, ".").rstrip(".py")
#     #
#     #                 try:
#     #                     print(module_name)
#     #                     print(sys.modules.get(module_name))
#     #                     if module_name in sys.modules:
#     #                         importlib.reload(sys.modules[module_name])
#     #                         print(f"Перезагружен модуль: {module_name}")
#     #                     else:
#     #                         print(f"Модуль не найден: {module_name}")
#     #                 except Exception as e:
#     #                     print(f"Ошибка при перезагрузке модуля {module_name}: {e}")
#
#     # await asyncio.sleep(0)  # Асинхронная пауза, чтобы избежать блокировки
#
#     # @staticmethod
#     # async def async_find_and_reload_modules(base_path):
#     #     for root, dirs, files in os.walk(base_path):
#     #         for file in files:
#     #             if file.endswith(".py") and file != "__init__.py":
#     #                 module_path = os.path.relpath(os.path.join(root, file), base_path)
#     #                 # module_name = module_path.replace(os.path.sep, ".").rstrip(".py")
#     #                 module_name = os.path.abspath(module_path).replace(os.path.sep, ".").rstrip(".py")
#     #
#     #                 print(module_name)
#     #
#     #                 try:
#     #                     module = importlib.import_module(module_name)
#     #                     print(module_name)
#     #                     print(module)
#     #                     importlib.reload(module)
#     #                     print(f"Перезагружен модуль: {module_name}")
#     #                 except Exception as e:
#     #                     print(f"Ошибка при перезагрузке модуля {module_name}: {e}")
#     #
#     #     await asyncio.sleep(0)  # Асинхронная пауза, чтобы избежать блокировки
#
#     # @staticmethod
#     # async def async_find_and_reload_modules(base_path):
#     #     for root, dirs, files in os.walk(base_path):
#     #         for file in files:
#     #             if file.endswith(".py") and file != "__init__.py":
#     #                 print("root: ", root)
#     #                 print("file: ", file)
#     #                 module_path = os.path.join(root, file)
#     #                 print(module_path)
#     #                 relative_path = os.path.relpath(module_path, base_path)
#     #                 module_name = relative_path.replace(os.path.sep, ".").rstrip(".py")
#     #
#     #                 print(module_name)
#     #
#     #                 try:
#     #                     module = importlib.import_module(f"core.{module_name}")
#     #                     print(module_name)
#     #                     print(module)
#     #                     importlib.reload(module)
#     #                     print(f"Перезагружен модуль: {module_name}")
#     #                 except Exception as e:
#     #                     print(f"Ошибка при перезагрузке модуля core.{module_name}: {e}")
#     #
#     #     await asyncio.sleep(0)  # Асинхронная пауза, чтобы избежать блокировки
#
#     @staticmethod
#     async def async_find_and_reload_modules(base_path):
#         ignore_folders = ["cogs", "cogs/commands", "cogs/events", "main", "main/config", "core/database", "core/database/models",
#                           "core/database/repositories"]
#         for root, dirs, files in os.walk(base_path):
#             print(root, dirs, files)
#             if any(folder in root for folder in ignore_folders):
#                 print(f"Skipping {root} due to ignore folder")
#                 continue
#
#             for file in files:
#                 if file.endswith(".py") and file != "__init__.py":
#                     module_path = os.path.join(root, file)
#                     relative_path = os.path.relpath(module_path, base_path)
#                     module_name = relative_path.replace(os.path.sep, ".").rstrip(".py")
#
#                     # Добавляем базовый путь к имени модуля
#                     module_name = f"{os.path.basename(base_path)}.{module_name}"
#                     print(module_name)
#
#                     try:
#                         module = importlib.import_module(module_name)
#                         print(module_name)
#                         print(module)
#                         importlib.reload(module)
#                         print(f"Перезагружен модуль: {module_name}")
#                     except Exception as e:
#                         print(f"Ошибка при перезагрузке модуля {module_name}: {e}")
#
#         await asyncio.sleep(0)  # Асинхронная пауза, чтобы избежать блокировки
#
#
# async def start_watching(ev_loop: asyncio.AbstractEventLoop, paths: list[str]):
#     observers = []
#     for path in paths:
#         if not os.path.exists(path):
#             print(f"Ошибка: Путь {path} не существует.")
#             continue
#
#         event_handler = AsyncFileChangeHandler(ev_loop, path)
#         observer = Observer()
#         observer.schedule(event_handler, path=path, recursive=True)
#         observer.start()
#         observers.append(observer)
#
#     try:
#         while True:
#             await asyncio.sleep(1)
#     except KeyboardInterrupt:
#         for observer in observers:
#             observer.stop()
#     for observer in observers:
#         observer.join()
#
#
# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#
#     loop.create_task(start_watching(loop, [
#         os.path.join(os.getcwd(), 'core'),
#         # os.path.join(os.getcwd(), 'core/cogs'),
#         # os.path.join(os.getcwd(), 'core/database'),
#         # os.path.join(os.getcwd(), 'core/misc'),
#     ]))
#
#     loop.run_until_complete(bot.run(settings.BOT_TOKEN))

import importlib
import os
import sys
import asyncio
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class AsyncFileChangeHandler(FileSystemEventHandler):
    def __init__(self, event_loop: asyncio.AbstractEventLoop, path: str):
        self.loop = event_loop
        self.base_path = path

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"Found changed file: {event.src_path}")
            self.event = event
            asyncio.run_coroutine_threadsafe(self.async_reload_on_change(), self.loop)

    async def async_reload_on_change(self):
        try:
            file_path = self.event.src_path
            # Получаем имя модуля
            relative_path = os.path.relpath(file_path, self.base_path)
            module_name = relative_path.replace(os.path.sep, '.').replace('.py', '')

            if module_name.startswith('.'):
                module_name = module_name[1:]

            # Полное имя модуля
            module_name = f'core.{module_name}'
            print(f"Reloading module: {module_name}")

            importlib.invalidate_caches()

            # Перезагружаем модуль и все его зависимости
            self.reload_all_modules()

            # re-initialize database
            from core.database import init_database
            await init_database()
            print(f"Reloaded all modules")

        except Exception as e:
            print(f"Error while reloading module: {e}")

    def reload_all_modules(self):
        # Перезагружаем все модули в sys.modules
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('core.'):
                try:
                    module = sys.modules[module_name]
                    importlib.reload(module)
                    print(f"Reloaded module: {module_name}")
                except Exception as e:
                    print(f"Error while reloading module {module_name}: {e}")


async def start_watching(ev_loop: asyncio.AbstractEventLoop, paths: list[str]):
    observers = []
    for path in paths:
        if not os.path.exists(path):
            print(f"Error: Path {path} does not exist.")
            continue

        event_handler = AsyncFileChangeHandler(ev_loop, path)
        observer = Observer()
        observer.schedule(event_handler, path=path, recursive=True)
        observer.start()
        observers.append(observer)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
    for observer in observers:
        observer.join()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    loop.create_task(start_watching(loop, [
        os.path.join(os.getcwd(), 'core'),
    ]))

    loop.run_until_complete(bot.run(settings.BOT_TOKEN))
