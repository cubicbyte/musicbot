"""
Модуль для работы с YouTube
"""

import sponsorblock as sb
from yt_dlp import YoutubeDL
from settings import YDL_OPTIONS
from ..schemas import YoutubeVideo

_sb_client = sb.Client()



def process_youtube_search(url_or_search: str) -> list[YoutubeVideo]:
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
            res.append(YoutubeVideo(**YoutubeVideo.extract_ydl(video)))
    else:
        res.append(YoutubeVideo(**YoutubeVideo.extract_ydl(ydl_res)))

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



def get_skip_segments(video_id: str) -> list[sb.Segment] | None:
    """
    Получить сегменты для пропуска из видео с помощью SponsorBlock.

    Используется для пропуска спонсорских вставок, интро и т.д.

    :param video_id: ID видео

    :return: Список сегментов
    """

    try:
        return _sb_client.get_skip_segments(video_id)
    except: #sb.errors.HTTPException:
        return None



def get_ffmpeg_sponsor_filter(segments: list[sb.Segment], vid_duration_s: int) -> str:
    """
    Получить аргументы ffmpeg для удаления сегментов SponsorBlock из видео.
    """

    skipped = len(segments)
    filter_complex = ''


    for i, segment in enumerate(segments):

        # Определить начало и конец обрезки видео
        if i == 0 and len(segments) != 1:
            start = 0
            end = int(segment.start)
        else:
            next_segment = segments[i + 1] if i + 1 < len(segments) else None
            start = int(segment.end)
            end = int(next_segment.start) if next_segment else vid_duration_s

        if end - start < 1 and len(segments) > 1:
            skipped -= 1
            continue

        segment_i = i + 1 - (len(segments) - skipped)
        filter_complex += f"[0:a]atrim={start}:{end},asetpts=PTS-STARTPTS[a{segment_i}];"


    for i in range(1, skipped + 1):
        filter_complex += f"[a{i}]"


    filter_complex += f"concat=n={skipped}:v=0:a=1[outa]"

    return f'-filter_complex "{filter_complex}" -map "[outa]"'
