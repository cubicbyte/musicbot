import os
import time
from .audio import AudioQueue
from .schemas import SpamState, Language
from .utils import load_lang_file



class LanguageManager:
    """
    Менеджер языков.

    Пример использования:
    >>> manager = LanguageManager('langs')
    >>> lang = manager.get_lang('ru')
    >>> print(lang.get('hello_world'))
    ... # "Привет, мир!" или "hello_world" в случае отсутствия ключа
    """

    _langs: dict[str, Language] = {}
    "Глобальный словарь языков"


    @staticmethod
    def load(path: str):
        "Загрузить языки из указанной директории"

        for file in os.listdir(path):
            lang = load_lang_file(f'{path}/{file}')
            LanguageManager._langs[lang.lang_code] = lang


    @staticmethod
    def get_lang(lang_code: str) -> Language:
        "Получить язык по его коду"

        return LanguageManager._langs.get(lang_code)



class GuildData:
    "Данные сервера"

    _global_data = {}
    "Глобальный словарь данных серверов"
    MOVE_CD_S = 0.75
    "Кулдаун перемещения бота между голосовыми каналами (в секундах)"


    def __init__(self, guild_id: int) -> None:

        self.guild_id = guild_id
        "ID сервера"
        self.spam: SpamState | None = None
        "Текуший спам"
        self.last_move_timestamp: float = 0
        "Время последнего перемещения бота между голосовыми каналами"


    @property
    def queue(self) -> AudioQueue:
        "Очередь музыки"

        return AudioQueue.get(self.guild_id)



    def get(guild_id: int) -> 'GuildData':
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
        if t - self.last_move_timestamp < GuildData.MOVE_CD_S:
            return False

        self.last_move_timestamp = t
        return True


    def delete(self):
        "Удалить данные сервера"

        self.queue.delete()
