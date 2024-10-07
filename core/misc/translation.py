import os
import asyncio
import time
from collections import defaultdict
from babel.support import Translations, NullTranslations, gettext as _
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core import logger


class TranslationManager:
    def __init__(self) -> None:
        """Initialize the TranslationManager with default settings."""
        self.locale_dir: str = os.path.join(os.path.dirname(__file__), "translations")
        self.languages: list[str] = self._get_available_languages()
        self.translations: dict[str, Translations | NullTranslations] = defaultdict()
        self.locale_mapping: dict[str, str] = {
            "id": "id",  # Indonesian
            "da": "da",  # Danish
            "de": "de",  # German
            "en-GB": "en",  # English (UK)
            "en-US": "en",  # English (US)
            "es-ES": "es",  # Spanish (Spain)
            "fr": "fr",  # French
            "hr": "hr",  # Croatian
            "it": "it",  # Italian
            "lt": "lt",  # Lithuanian
            "hu": "hu",  # Hungarian
            "nl": "nl",  # Dutch
            "no": "no",  # Norwegian
            "pl": "pl",  # Polish
            "pt-BR": "pt_BR",  # Portuguese (Brazil)
            "ro": "ro",  # Romanian
            "fi": "fi",  # Finnish
            "sv-SE": "sv",  # Swedish
            "vi": "vi",  # Vietnamese
            "tr": "tr",  # Turkish
            "cs": "cs",  # Czech
            "el": "el",  # Greek
            "bg": "bg",  # Bulgarian
            "ru": "ru",  # Russian
            "uk": "uk",  # Ukrainian
            "hi": "hi",  # Hindi
            "th": "th",  # Thai
            "zh-CN": "zh_CN",  # Chinese (China)
            "ja": "ja",  # Japanese
            "zh-TW": "zh_TW",  # Chinese (Taiwan)
            "ko": "ko",  # Korean
        }

        self.observer = Observer()
        self.event_handler = TranslationChangeHandler(self)
        self.observer.schedule(self.event_handler, self.locale_dir, recursive=True)
        self.observer.start()

        self.load_translations()
        self.logger = logger.bind(source=self.__class__.__module__)
        # asyncio.create_task(self.load_translations())

    def _get_available_languages(self) -> list[str]:
        """Get a list of available languages from the translations directory."""
        available_languages = []
        for item in os.listdir(self.locale_dir):
            if os.path.isdir(os.path.join(self.locale_dir, item)):
                available_languages.append(item)
        return available_languages

    def load_translations(self, langs: list[str] | None = None) -> None:
        """Load translations for all available languages."""
        if langs is None:
            langs = self.languages

        for lang in langs:
            try:
                translations = Translations.load(self.locale_dir, [lang])
                self.translations[lang] = translations
            except Exception as e:
                self.logger.error(f"Failed to load translations for {lang}: {e}")

    def reload_translations(self, lang: list[str] | str | None = None) -> None:
        """Reload translations for all available languages."""
        if lang is None:
            langs = self.languages
        elif isinstance(lang, str):
            langs = [lang]

        self.translations.clear()
        self.load_translations(langs)
        self.logger.info(f"Translations reloaded for {lang}")

    async def get_translation(self, lang: str, text: str) -> str:
        """Get the translation for a given text in the specified language.

        :param lang: The language code.
        :param text: The text to be translated.
        :return: The translated text.
        """
        lang = self.locale_mapping.get(lang, lang)

        return (
            self.translations[lang].gettext(text) if lang in self.translations else text
        )

    async def get(self, lang: str, text: str) -> str:
        """Get the translation for a given text in the specified language.

        This is a shortcut for get_translation method.
        """
        return await self.get_translation(lang, text)

    def add_language(self, lang: str) -> None:
        """Add a new language to the manager.

        :param lang: The language code to be added.
        """
        if lang not in self.languages:
            self.languages.append(lang)

    def remove_language(self, lang: str) -> None:
        """Remove a language from the manager.

        :param lang: The language code to be removed.
        """
        if lang in self.languages:
            self.languages.remove(lang)
            if lang in self.translations:
                del self.translations[lang]

    def available_locales(self) -> list[str]:
        """Get a list of available translation locales.

        :return: A list of locale codes.
        """
        return self.languages

    def __del__(self):
        self.observer.stop()
        self.observer.join()


class TranslationChangeHandler(FileSystemEventHandler):
    def __init__(self, translation_manager: TranslationManager):
        self.translation_manager: TranslationManager = translation_manager
        self.logger = logger.bind(source=self.__class__.__module__)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".mo"):
            lang = event.src_path.split("/")[-3]
            self.logger.debug(f"Reloading translations for {lang}")
            self.translation_manager.reload_translations(lang)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".mo"):
            lang = event.src_path.split("/")[-3]
            self.logger.debug(f"Reloading translations for {lang}")
            self.translation_manager.reload_translations(lang)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(".mo"):
            lang = event.src_path.split("/")[-3]
            self.logger.debug(f"Reloading translations for {lang}")
            self.translation_manager.reload_translations(lang)
