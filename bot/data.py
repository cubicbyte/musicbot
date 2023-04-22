"""
Модуль для работы с различными данными
"""

import os
import time
import json
import sqlite3
from settings import LANGS_DIR
from .audio import AudioQueue
from .schemas import SpamState, Language, YoutubeVideo
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

        self._db.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY,
                lang_code TEXT,
                saves JSON
            );
        ''')
        self._db.commit()


    @staticmethod
    def _saves_deserializer(_dict: dict) -> dict[str, YoutubeVideo]:
        """
        Десериализатор для сохранённых песен

        Короче штука, которая парсит песни с базы данных, сохранённые в формате json,
        и преобразует их в читаемый для программы формат
        """

        if 'title' in _dict:
            return YoutubeVideo(**_dict)

        return _dict


    def _get_field(self, guild_id: int, field: str) -> str | None:
        "Получить значение поля из таблицы по ключу"

        row = self._db.execute(
            f'SELECT {field} FROM guilds WHERE guild_id = ?',
            (guild_id,)).fetchone()

        if row is None:
            return None

        return row[field]


    def _set_field(self, guild_id: int, field: str, value: any) -> None:
        "Установить значение поля в таблице по ключу"

        self._db.execute(
            f'INSERT OR REPLACE INTO guilds (guild_id, {field}) VALUES (?, ?)',
            (guild_id, value))

        self._db.commit()


    def get_guild_lang(self, guild_id: int) -> str | None:
        "Получить язык сервера"
        return self._get_field(guild_id, 'lang_code')

    def set_guild_lang(self, guild_id: int, lang_code: str) -> None:
        "Установить язык сервера"
        self._set_field(guild_id, 'lang_code', lang_code)


    def get_guild_yt_saves(self, guild_id: int) -> dict[str, YoutubeVideo]:
        "Получить список сохранённых песен"

        res = self._get_field(guild_id, 'saves')
        if res is None:
            return {}

        saves = json.loads(res, object_hook=self._saves_deserializer)
        return saves

    def set_guild_yt_saves(self, guild_id: int, saves: dict[str, YoutubeVideo]) -> None:
        "Установить список сохранённых песен"
        json_str = json.dumps(saves, default=lambda o: o.__dict__)
        self._set_field(guild_id, 'saves', json_str)



class GuildData:
    "Данные сервера"


    MOVE_CD_S = 0.75
    "Кулдаун перемещения бота между голосовыми каналами (в секундах)"

    _global_data = {}
    "Глобальный словарь данных серверов"
    _database: BotDatabase
    "База данных для хранения постоянных данных"


    def __init__(self, guild_id: int) -> None:
        self.guild_id = guild_id
        "ID сервера"
        self.spam: SpamState | None = None
        "Текуший спам"
        self._last_move_timestamp: float = 0
        "Время последнего перемещения бота между голосовыми каналами"
        self._lang_code: str = self._database.get_guild_lang(guild_id) or os.getenv('DEFAULT_LANG')
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
        self._database.set_guild_lang(self.guild_id, value)


    @property
    def lang(self) -> Language:
        "Язык сервера"
        return langs[self._lang_code]



database: 'BotDatabase' = BotDatabase('bot-data.sqlite')
"База данных для хранения постоянной информации"
langs: dict[str, Language] = _load_langs(LANGS_DIR)
"Словарь языков"

GuildData._database = database



# Проверка верность языка по умолчанию
assert os.getenv('DEFAULT_LANG') in langs, (
    f'Поле DEFAULT_LANG в файле .env имеет несуществующий язык: {os.getenv("DEFAULT_LANG")}. Список доступных языков: ({", ".join(langs.keys())})')
