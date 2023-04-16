from yt_dlp import YoutubeDL
from settings import YDL_OPTIONS
from ..schemas import YoutubeVideo



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
