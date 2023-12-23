"""
Module for working with YouTube, like searching videos, getting audio from videos, etc.
"""

import sponsorblock as sb

from yt_dlp import YoutubeDL
from settings import YDL_OPTIONS
from bot.schemas import YoutubeVideo

_sb_client = sb.Client()


def process_youtube_search(url_or_search: str) -> list[YoutubeVideo]:
    """
    Returns list of `YoutubeVideo` from link or search query.

    If link to playlist is passed, then returns list of all videos from playlist,
    else returns list with one video.

    :param url_or_search: Link to video or search query

    :returns: List of `YoutubeVideo`
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
    Get information about video from YouTube.

    :return: Result of `YoutubeDL().extract_info`
    """

    with YoutubeDL(YDL_OPTIONS) as ydl:
        ydl_res = ydl.extract_info(url_or_search, download=False)

    return ydl_res


def get_skip_segments(video_id: str) -> list[sb.Segment] | None:
    """
    Get segments to skip from video using SponsorBlock.

    Used to skip sponsor inserts, intros, etc.

    :param video_id: Youtube video ID (/watch?v=...)

    :return: List of segments
    """

    try:
        return _sb_client.get_skip_segments(video_id)
    except sb.errors.HTTPException:
        return None


def get_ffmpeg_sponsor_filter(segments: list[sb.Segment], vid_duration_s: int) -> str:
    """
    Get ffmpeg arguments for removing SponsorBlock segments from video.

    Works by trimming parts of audio track that do not contain segments,
    with subsequent concatenation.
    """

    filter_complex = ''
    count_of_segments = 0

    # Include interval between video start and first segment
    start = 0
    end = segments[0].start
    if end - start > 1:
        filter_complex += f"[0:a]atrim={start}:{end},asetpts=PTS-STARTPTS[a0];"
        count_of_segments += 1

    # Include intervals between other segments
    for i, segment in enumerate(segments):
        # Determine start and end of video trimming
        next_segment = segments[i + 1] if i + 1 < len(segments) else None
        start = segment.end
        end = next_segment.start if next_segment else vid_duration_s

        # If interval is too small, then skip it
        if end - start < 1 and len(segments) > 1:
            continue

        filter_complex += f"[0:a]atrim={start}:{end},asetpts=PTS-STARTPTS[a{count_of_segments}];"
        count_of_segments += 1

    for i in range(count_of_segments):
        filter_complex += f"[a{i}]"

    filter_complex += f"concat=n={count_of_segments}:v=0:a=1[outa]"

    return f'-filter_complex "{filter_complex}" -map "[outa]"'
