"""
Module with all data schemas used in bot
"""

from asyncio import sleep
from dataclasses import dataclass


class Language(dict):
    """
    Language dictionary wrapper.

    Returns key if it's not in dictionary, has `lang_code` property.
    """

    def __init__(
            self,
            lang: dict[str, str] | None = None,
            code: str | None = None
    ) -> None:
        """
        :param lang: Language dictionary
        :param code: Language code
        """

        super().__init__(lang or {})

        self.lang_code = code
        "Language code"

    def __str__(self) -> str | None:
        return self.lang_code

    def __missing__(self, __key: str) -> str:
        return __key

    def get(self, __key: str) -> str:
        return self[__key]


@dataclass
class SpamState:
    """Spam state class.

    >>> spam = SpamState('@nazar067 join vc', 20, 0.5)
    >>> async for text in spam:
    ...     await ctx.send(text)
    """

    text: str
    "Text to spam"
    repeats: int
    "Repeat count"
    delay: float
    "Delay between messages in seconds"
    progress: int = 0
    "Current progress"

    async def __aiter__(self):
        """Async iterator for spam state.

        >>> async for _ in spam:
        ...     # do something
        ...     ...
        """

        while self.progress < self.repeats:
            yield self.text, self.progress

            self.progress += 1
            await sleep(self.delay)

    def stop(self):
        """Stop spamming"""

        self.progress = self.repeats


@dataclass
class AudioSource:
    """Base class for audio sources."""

    source_url: str
    "Direct link to audio file, playble by `discord.FFmpegPCMAudio`"


@dataclass
class YoutubeVideo(AudioSource):
    """Class for storing information about youtube video."""

    origin_query: str
    "Original search query"
    id: str
    "Video ID (https://www.youtube.com/watch?v= `tPEE9ZwTmy0`)"
    title: str
    "Video title"
    author: str
    "Video author"
    description: str
    "Video description"
    duration: int
    "Video duration in seconds"
    duration_str: str
    "Video duration in format `MM:SS` / `HH:MM:SS` / `DD:HH:MM:SS`"
    thumbnail: str
    "Link to video thumbnail"

    @staticmethod
    def extract_ydl(vid_info: dict[str, any]) -> 'YoutubeVideo':
        """Extract video information from `YoutubeDL.extract_info` dictionary"""

        return dict(
            source_url=vid_info.get('url'),
            origin_query=vid_info.get('original_url'),
            id=vid_info.get('id'),
            title=vid_info.get('title'),
            author=vid_info.get('uploader'),
            description=vid_info.get('description'),
            duration=vid_info.get('duration'),
            duration_str=vid_info.get('duration_string'),
            thumbnail=vid_info.get('thumbnail'),
        )

    @property
    def url(self) -> str:
        """Video URL"""
        return f'https://www.youtube.com/watch?v={self.id}'
