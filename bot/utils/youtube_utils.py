"""
Модуль для работы с YouTube
"""

import sponsorblock as sb
from yt_dlp import YoutubeDL
from settings import YDL_OPTIONS
from ..schemas import SponsorBlockVideo

_sb_client = sb.Client()



def process_youtube_search(url_or_search: str) -> list[SponsorBlockVideo]:
    """
    Возвращает список `YoutubeVideo` из ссылки или поискового запроса.

    Если передана ссылка на плейлист, то возвращается список всех видео из плейлиста,
    иначе возвращается список с одним видео.

    :param url_or_search: Ссылка на видео или поисковый запрос

    :return: Список `YoutubeVideo`
    """

    ydl_res = search_youtube(url_or_search)
    res = []

    if ydl_res.get('_type') == 'playlist':
        for video in ydl_res['entries']:
            video['original_url'] = ydl_res.get('original_url')
            segments = get_skip_segments(video['id'])
            res.append(SponsorBlockVideo(**SponsorBlockVideo.extract_ydl(video), segments=segments))
    else:
        segments = get_skip_segments(ydl_res['id'])
        res.append(SponsorBlockVideo(**SponsorBlockVideo.extract_ydl(ydl_res), segments=segments))

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



def get_skip_segments(video_id: str) -> list[sb.Segment]:
    """
    Получить сегменты для пропуска из видео с помощью SponsorBlock.

    Используется для пропуска спонсорских вставок, интро и т.д.

    :param video_id: ID видео

    :return: Список сегментов
    """

    return _sb_client.get_skip_segments(video_id)
