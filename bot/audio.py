"""
Module for working with audio
"""

from discord import VoiceClient, FFmpegPCMAudio
from settings import FFMPEG_OPTIONS
from bot import youtube
from bot.schemas import AudioSource, YoutubeVideo


class AudioQueue(list):
    """
    Audio queue manager
    """

    _global_queue: dict[str, 'AudioQueue'] = {}
    "Global queue mapping for all servers"

    @classmethod
    def get_queue(cls, guild_id: int) -> 'AudioQueue':
        """Get queue for server"""

        _guild_id = str(guild_id)
        queue = cls._global_queue.get(_guild_id)

        # Create queue if it doesn't exist
        if queue is None:
            queue = AudioQueue(guild_id)
            cls._global_queue[_guild_id] = queue

        return queue

    @classmethod
    def del_queue(cls, guild_id: int):
        """Delete queue from global queue list"""

        _guild_id = str(guild_id)

        if _guild_id in cls._global_queue:
            del cls._global_queue[_guild_id]

    def __init__(self, guild_id: int) -> None:
        super().__init__()

        self.guild_id: int = guild_id
        "Server ID"
        self.on_replay: bool = False
        "Audio replay flag"
        self._current: AudioSource | None = None
        "Current audio"
        self._latest: AudioSource | None = None
        "Latest played audio"

    @property
    def full_queue(self) -> list[AudioSource]:
        """Queue with current audio included"""

        if self.current is None:
            return self.copy()

        return [self.current, *self]

    def delete(self):
        """Delete queue from global queue list"""
        AudioQueue.del_queue(self.guild_id)

    def skip(self, count: int = 1):
        """Skip audio"""

        for _ in range(count):
            if len(self) == 0:
                self.current = None
                break

            self.current = self.pop(0)

    def next(self) -> AudioSource | None:
        """Get next audio"""

        if not self.on_replay or self.current is None:
            self.skip()

        return self.current

    def set_next(self, audio: AudioSource | list[AudioSource]):
        """Set next audio"""

        if isinstance(audio, list):
            for i, aud in enumerate(audio):
                self.insert(i, aud)
        else:
            self.insert(0, audio)

    @property
    def latest(self) -> AudioSource | None:
        """Latest played audio"""
        return self._latest

    @property
    def current(self) -> AudioSource | None:
        """Current audio"""
        return self._current

    @current.setter
    def current(self, value: AudioSource | None):
        self._latest = self.current or self._latest or value
        self._current = value


class AudioController:
    """
    Audio playback controller.

    Is a wrapper over `VoiceClient` for convenient playback control.

    Supports the following functionality:

    - Audio queue
    - Audio replay
    - Playback control (play, stop, skip)
    """

    _controllers = {}

    @classmethod
    def get_controller(cls, voice_client: VoiceClient) -> 'AudioController':
        """Get controller for server"""

        cont = cls._controllers.get(voice_client.guild.id)

        # Create controller if it doesn't exist
        if cont is None:
            cont = AudioController(voice_client)
            cls._controllers[voice_client.guild.id] = cont

        return cont

    def __init__(self, voice_client: VoiceClient) -> None:
        self.voice_client = voice_client
        self._loop_running = False
        "Flag for stopping audio playback loop"

    def _play_loop(self, error: any = None) -> None:
        """
        Recursive function for playing audio.

        Passed to `after` argument of `VoiceClient.play` method
        """

        # Flag for stopping loop
        if not self._loop_running:
            return

        next_audio = self.queue.next()

        # Stop loop if queue is empty
        if next_audio is None:
            self._loop_running = False
            return

        self._play_audio(next_audio)

    def _play_audio(self, audio: AudioSource):
        """Play audio by bot"""

        ffmpeg_options = FFMPEG_OPTIONS.copy()

        # Use filter for sponsor segments (SponsorBlock integration)
        if isinstance(audio, YoutubeVideo):
            ffmpeg_options.setdefault('options', '')
            segments = youtube.get_skip_segments(audio.id)

            if segments is not None:
                opts = youtube.get_ffmpeg_sponsor_filter(segments, audio.duration)
                ffmpeg_options['options'] += ' ' + opts

        self.voice_client.play(
            FFmpegPCMAudio(audio.source_url, **ffmpeg_options),
            after=self._play_loop
        )

    def start(self):
        """Start audio playback loop"""

        self._loop_running = True
        self._play_loop()

    def stop(self):
        """Stop audio playback loop"""

        self._loop_running = False
        self.voice_client.stop()

    def skip(self, count: int = 1):
        """Skip audio in queue"""

        self.queue.skip(count - 1)

        if self.voice_client.is_playing():
            self.voice_client.stop()
        else:
            self.start()

    def play_audio(self, audio: AudioSource | list[AudioSource]):
        """Force play audio"""

        self.queue.set_next(audio)

        if self.voice_client.is_playing():
            self.voice_client.stop()
        else:
            self.start()

    @property
    def queue(self) -> AudioQueue:
        """Audio queue"""

        return AudioQueue.get_queue(self.voice_client.guild.id)
