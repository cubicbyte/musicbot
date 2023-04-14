"""
Модуль с различными вспомогательными функциями
"""

from ast import literal_eval
from pathlib import Path
from urllib.parse import urlparse
from yt_dlp import YoutubeDL
from discord import VoiceState, VoiceChannel
from discord.ext.commands import Bot
from settings import YDL_OPTIONS
from .schemas import Language, YoutubeVideo



def load_lang_file(path: str) -> Language:
    """
    Загрузить файл .lang

    ### Пример использования::

        >>> lang = load_lang_file('langs/ru.lang')
        >>> print(lang['hello_world'])
        ... # Привет, мир!
        >>> print(lang['unexisting_key'])
        ... # unexisting_key (потому что ключа нет в словаре)

    ### Формат файла::

        # Комментарий
        # Комментарий с символом # внутри

        # Пустая строка выше ^
        hello_world=Привет, мир!
        error.something_went_wrong=Что-то пошло не так
        любой ключ перед знаком равно=любое значение с любыми символами

    :param path: Путь к файлу
    """

    lang = Language(lang_code=Path(path).stem)

    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line[:-1]                # Убрать символ переноса строки
            line = unescape_string(line)    # Преобразовать экранированные символы в нормальные (e.g. \\n -> \n)

            if line == '' or line.startswith('#'):
                continue

            try:
                key, value = line.split('=', 1)
            except ValueError:
                raise SyntaxError(f'invalid line {i + 1} in {path}:\n"{line}"')

            lang[key] = value

    return lang



def process_youtube_search(url_or_search: str) -> list[YoutubeVideo]:
    """
    Возвращает список `YoutubeVideo` из ссылки или поискового запроса.

    Если передана ссылка на плейлист, то возвращается список всех видео из плейлиста,
    иначе возвращается список с одним видео.\n\n

    :param url_or_search: Ссылка на видео или поисковый запрос

    :return: Список `YoutubeVideo`
    """

    ydl_res = search_youtube(url_or_search)
    res = []

    if ydl_res.get('_type') == 'playlist':
        for video in ydl_res['entries']:
            res.append(YoutubeVideo.from_ydl(video))
    else:
        res.append(YoutubeVideo.from_ydl(ydl_res))

    return res



def search_youtube(url_or_search: str) -> dict[str, any]:
    """
    Получить информацию о видео с YouTube.

    :return: Результат `YoutubeDL().extract_info`
    """

    # Получаем информацию о видео
    with YoutubeDL(YDL_OPTIONS) as ydl:
        ydl_res = ydl.extract_info(url_or_search, download=False)

    return ydl_res



def unescape_string(escaped_string: str) -> str:
    "Преобразовать строку с экранированными символами (e.g. \\n) в нормальную строку"

    return literal_eval(f'"{escaped_string}"')



def is_url(string: str) -> bool:
    "Проверить, является ли строка ссылкой"

    try:
        r = urlparse(string)
    except ValueError:
        return False

    return all([r.scheme, r.netloc])


def is_users_in_channel(channel: VoiceChannel):
    "Проверить, есть ли в голосовом канале пользователи. Боты не учитываются."

    for member in channel.members:
        if not member.bot:
            return True

    return False



def is_connected(bot: Bot, channel: VoiceChannel):
    "Проверить, подключён ли бот к голосовому каналу"

    for member in channel.members:
        if member.id == bot.user.id:
            return True

    return False



def get_bot_channel(bot: Bot, *states: VoiceState | None) -> VoiceChannel | None:
    "Получить голосовой канал, в котором находится бот"

    for state in states:
        if state is None or state.channel is None:
            continue

        if is_connected(bot, state.channel):
            return state.channel

    return None
