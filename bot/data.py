"""
Модуль для работы с различными данными
"""

import os
import time
import sqlite3
from settings import LANGS_DIR
from .audio import AudioQueue
from .schemas import SpamState, Language
from .utils import load_lang_file



def _load_langs(path: str) -> dict[str, Language]:
    "Загрузить языки из указанной директории"

    langs = {}

    for file in os.listdir(path):
        # Загружать только файлы .lang
        if not file.endswith('.lang'):
            continue

        lang = load_lang_file(f'{path}/{file}')
        langs[lang.lang_code] = lang

    return langs



class BotDatabase:
    "База данных для хранения постоянной информации"


    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_db()


    def _init_db(self):
        "Инициализировать базу данных"

        self._db.execute('CREATE TABLE IF NOT EXISTS guilds (guild_id INTEGER PRIMARY KEY, lang_code TEXT)')
        self._db.commit()


    def get_guild_lang(self, guild_id: int) -> str | None:
        "Получить язык сервера"

        row = self._db.execute('SELECT lang_code FROM guilds WHERE guild_id = ?', (guild_id,)).fetchone()
        return row['lang_code']


    def set_guild_lang(self, guild_id: int, lang_code: str) -> None:
        "Установить язык сервера"

        self._db.execute(
            'INSERT OR REPLACE INTO guilds (guild_id, lang_code) VALUES (?, ?)',
            (guild_id, lang_code)
        )
        self._db.commit()



class GuildData:
    "Данные сервера"

    _global_data = {}
    "Глобальный словарь данных серверов"
    MOVE_CD_S = 0.75
    "Кулдаун перемещения бота между голосовыми каналами (в секундах)"
    database: BotDatabase
    "База данных для хранения постоянных данных"


    def __init__(self, guild_id: int) -> None:
        self.guild_id = guild_id
        "ID сервера"
        self.spam: SpamState | None = None
        "Текуший спам"
        self._last_move_timestamp: float = 0
        "Время последнего перемещения бота между голосовыми каналами"
        self._lang_code: str = self.database.get_guild_lang(guild_id) or os.getenv('DEFAULT_LANG')
        "Код языка сервера"


    @property
    def queue(self) -> AudioQueue:
        "Очередь музыки"
        return AudioQueue.get_queue(self.guild_id)


    @staticmethod
    def get_instance(guild_id: int) -> 'GuildData':
        "Получить экземпляр класса GuildData для сервера с указанным ID"

        _guild_id = str(guild_id)
        gd = GuildData._global_data.get(_guild_id)

        # Зарегистрировать новый экземпляр, если нужно
        if gd is None:
            gd = GuildData(guild_id)
            GuildData._global_data[_guild_id] = gd

        return gd


    def create_spam(self, message: str, repeats: int, delay: float) -> SpamState:
        "Зарегистрировать новый экземпляр класса `SpamState`"
        self.spam = SpamState(message, repeats, delay)
        return self.spam


    def make_move(self) -> bool:
        "Зарегистрировать перемещение бота в голосовой канал и вернуть True, если кулдаун прошёл"

        t = time.time()
        if t - self._last_move_timestamp < GuildData.MOVE_CD_S:
            return False

        self._last_move_timestamp = t
        return True


    def delete(self):
        "Удалить данные сервера"
        self.queue.delete()


    @property
    def lang_code(self) -> str:
        "Код языка сервера"
        return self._lang_code


    @lang_code.setter
    def lang_code(self, value: str) -> None:
        "Установить код языка сервера"
        self._lang_code = value
        self.database.set_guild_lang(self.guild_id, value)


    @property
    def lang(self) -> Language:
        "Язык сервера"
        return langs[self._lang_code]



database: 'BotDatabase' = BotDatabase('bot-data.sqlite')
"База данных для хранения постоянной информации"
langs: dict[str, Language] = _load_langs(LANGS_DIR)
"Словарь языков"

GuildData.database = database



# Проверка верность языка по умолчанию
assert os.getenv('DEFAULT_LANG') in langs, (
    f'Поле DEFAULT_LANG в файле .env имеет несуществующий язык: {os.getenv("DEFAULT_LANG")}. Список доступных языков: ({", ".join(langs.keys())})')
