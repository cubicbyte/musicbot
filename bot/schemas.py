"""
Модуль со всеми схемами данных, используемых в боте
"""

import sponsorblock as sb
from asyncio import sleep
from dataclasses import dataclass



class Language(dict):
    """
    Обёртка вокруг языкового словаря.\n
    При отсутствии ключа в словаре возвращает сам ключ, имеет свойство `lang_code`.
    """


    def __init__(
        self,
        lang: dict[str, str] = {},
        lang_code: str | None = None
    ) -> None:
        """
        :param lang: Языковой словарь
        :param lang_code: Код языка
        """

        super().__init__(lang)

        self.lang_code = lang_code
        "Код языка"


    def __str__(self) -> str | None:
        return self.lang_code


    def __missing__(self, __key: str) -> str:
        return __key


    def get(self, __key: str) -> str:
        return self[__key]



@dataclass
class SpamState:
    """Состояние спама.

    >>> spam = SpamState('@nazar067 зайди в канал', 20, 0.5)
    >>> async for text in spam:
    ...     await ctx.send(text)
    """

    text:       str
    "Текст спама"
    repeats:    int
    "Количество повторений"
    delay:      float
    "Задержка между повторениями в секундах"
    progress:   int = 0
    "Текущий прогресс"


    async def __aiter__(self):
        """Асинхронный итератор для спама.

        >>> async for _ in spam:
        ...     # do something
        ...     ...
        """

        while self.progress < self.repeats:
            yield self.text, self.progress

            self.progress += 1
            await sleep(self.delay)


    def stop(self):
        "Остановить спам"

        self.progress = self.repeats



@dataclass
class AudioSource:
    "Класс для хранения информации о аудио-файле."

    source_url: str
    "Прямая ссылка на файл с аудиодорожкой"



@dataclass
class YoutubeVideo(AudioSource):
    "Класс для хранения информации о видео."

    origin_query: str
    "Оригинальный запрос поиска"
    id: str
    "ID видео (https://www.youtube.com/watch?v= `tPEE9ZwTmy0`)"
    title: str
    "Название видео"
    author: str
    "Автор видео"
    description: str
    "Описание видео"
    duration: int
    "Длительность видео в секундах"
    duration_str: str
    "Длительность видео в формате `ММ:СС` / `ЧЧ:ММ:СС` / `ДД:ЧЧ:ММ:СС`"
    thumbnail: str
    "Ссылка на превью видео"


    @staticmethod
    def extract_ydl(vid_info: dict[str, any]) -> 'YoutubeVideo':
        "Извлечь информацию о видео из словаря `YoutubeDL.extract_info`"

        return dict(
            source_url=vid_info.get('url'),
            origin_query=vid_info.get('original_url'),
            id=vid_info.get('id'),
            title=vid_info.get('title'),
            author=vid_info.get('uploader'),
            description=vid_info.get('description'),
            duration=vid_info.get('duration'),
            duration_str=vid_info.get('duration_str'),
            thumbnail=vid_info.get('thumbnail'),
        )

    @property
    def url(self) -> str:
        "Ссылка на видео"
        return f'https://www.youtube.com/watch?v={self.id}'



@dataclass
class SponsorBlockVideo(YoutubeVideo):
    "Расширение класса `YoutubeVideo` с информацией о сегментах SponsorBlock."

    segments: list[sb.Segment]
    "Список сегментов SponsorBlock"
