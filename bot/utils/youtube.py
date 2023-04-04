import re
import urllib.parse
import urllib.request
from yt_dlp import YoutubeDL
from . import is_url
from config import YDL_OPTIONS


def search_youtube(url_or_search: str) -> dict[str, any]:
    """
    Поиск на YouTube.

    :return: Результат `YoutubeDL().extract_info`
    """

    # Получаем информацию о видео
    with YoutubeDL(YDL_OPTIONS) as ydl:
        ydl_res = ydl.extract_info(url_or_search, download=False)

    return ydl_res

def url_to_id(url: str) -> str:
    "Преобразовать ссылку на видео YouTube в ID видео"
    return re.findall(r"watch\?v=(\S{11})", url)[0]


def search_to_id(search: str) -> str:
    "Преобразовать поисковый запрос в ID видео YouTube"
    search = urllib.parse.quote_plus(search) # Закодировать поисковую строку в URL
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    return video_ids[0]


def search_to_url(search: str) -> str:
    "Преобразовать поисковый запрос в ссылку на видео YouTube"
    return 'https://www.youtube.com/watch?v=' + search_to_id(search)
