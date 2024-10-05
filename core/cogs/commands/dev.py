import gettext
from disnake.ext import commands
from core.misc.embed import CustomEmbed
from core.misc.views.dev.bot_manager import DevBotManagerView
from core.misc.views.dev.console import DevConsoleView
from core.misc.views.dev.main import DevMainView
import os
import aiofiles
from babel import Locale
from babel.support import Translations


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Dev, self).__init__()
        self.bot = bot

    @staticmethod
    def embed():
        embed = CustomEmbed(
            title="👔 | Dev Panel",
            description="Welcome to the Dev Panel. Use the buttons below to navigate.",
        ).get_embed()
        return embed

    async def load_translations(self, locale_code):
        mo_file_path = os.path.join('locale', f'{locale_code}.mo')
        if not os.path.exists(mo_file_path):
            print(f"Файл {mo_file_path} не найден, используется английский по умолчанию.")
            mo_file_path = os.path.join('locale', 'en.mo')
        else:
            print(f"Загружается файл перевода: {mo_file_path}")
        translations = Translations.load(dirname='locale', locales=[locale_code])
        return translations

    async def cog_load(self):
        self.bot.add_view(DevMainView(self.bot))
        self.bot.add_view(DevBotManagerView(self.bot))
        self.bot.add_view(DevConsoleView(self.bot))

    @commands.slash_command(name="dev", dm_permission=True)
    async def dev(self, interaction):
        await interaction.send(
            embed=self.embed(), ephemeral=True, view=DevMainView(self.bot)
        )

    @commands.slash_command(name="translate", dm_permission=True)
    async def translate(self, interaction):
        user_locale = interaction.locale
        loc = Localization(locales_dir='locales', default_locale='en')

        loc.set_language(user_locale)
        title = loc.gettext("Hello")
        description = loc.gettext("World")
        embed = CustomEmbed(title=title, description=description).get_embed()
        await interaction.response.send_message(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Dev(bot))

class Localization:
    def __init__(self, locales_dir='locales', default_locale='en'):
        """
        Инициализация класса локализации.

        :param locales_dir: Каталог, в котором хранятся .mo файлы.
        :param default_locale: Локаль по умолчанию, если локаль пользователя не найдена.
        """
        self.locales_dir = locales_dir
        self.default_locale = default_locale
        self.translations = {}

    def load_translation(self, locale_code):
        """
        Загружает перевод для указанной локали, используя gettext.

        :param locale_code: Код локали (например, 'ru', 'en').
        :return: Объект gettext или None, если перевод не найден.
        """
        mo_file_path = os.path.join(self.locales_dir, f'{locale_code}.mo')

        if not os.path.exists(mo_file_path):
            mo_file_path = os.path.join(self.locales_dir, f'{self.default_locale}.mo')

        try:
            # Загружаем перевод
            translation = gettext.GNUTranslations(open(mo_file_path, 'rb'))
        except FileNotFoundError:
            # Если файл перевода не найден, используем пустой перевод
            translation = gettext.NullTranslations()

        self.translations[locale_code] = translation
        return translation

    def set_language(self, locale_code):
        """
        Устанавливает язык для перевода, используя gettext.install.

        :param locale_code: Код локали (например, 'ru', 'en').
        """
        translation = self.load_translation(locale_code)
        translation.install()

    def gettext(self, text, locale_code=None):
        """
        Переводит строку на указанный язык.

        :param text: Текст для перевода.
        :param locale_code: Код локали (если None, используется язык по умолчанию).
        :return: Переведённая строка.
        """
        if locale_code is None:
            locale_code = self.default_locale

        if locale_code not in self.translations:
            self.load_translation(locale_code)

        translation = self.translations[locale_code]
        return translation.gettext(text)