"""
Модуль для работы с музыкой
"""

from discord import VoiceClient, FFmpegPCMAudio
from settings import FFMPEG_OPTIONS
from bot.schemas import AudioSource, YoutubeVideo
from bot.utils import youtube_utils


class AudioQueue(list):
    """
    Очередь музыки
    """

    _global_queue: dict[str, 'AudioQueue'] = {}
    "Глобальный словарь очередей для всех серверов"

    @classmethod
    def get_queue(cls, guild_id: int) -> 'AudioQueue':
        """Получить очередь для отдельного сервера"""

        _guild_id = str(guild_id)
        queue = cls._global_queue.get(_guild_id)

        # Создать очередь, если её нету
        if queue is None:
            queue = AudioQueue(guild_id)
            cls._global_queue[_guild_id] = queue

        return queue

    @classmethod
    def del_queue(cls, guild_id: int):
        """Удалить очередь из глобального списка для очистки памяти"""

        _guild_id = str(guild_id)

        if _guild_id in cls._global_queue:
            del cls._global_queue[_guild_id]

    def __init__(self, guild_id: int) -> None:
        self.guild_id: int = guild_id
        "ID сервера"
        self.on_replay: bool = False
        "Автоповтор музыки"
        self._current: AudioSource | None = None
        "Текущая музыка"
        self._latest: AudioSource | None = None
        "Последняя проигранная музыка"

    @property
    def full_queue(self) -> list[AudioSource]:
        """Очередь с учётом текущей музыки"""

        if self.current is None:
            return self.copy()

        return [self.current, *self]

    def delete(self):
        """Удалить очередь из глобального списка для очистки памяти"""
        AudioQueue.del_queue(self.guild_id)

    def skip(self, count: int = 1):
        """Пропустить музыку"""

        for _ in range(count):
            if len(self) == 0:
                self.current = None
                break

            self.current = self.pop(0)

    def next(self) -> AudioSource | None:
        """Следующая музыка"""

        if not self.on_replay or self.current is None:
            self.skip()

        return self.current

    def set_next(self, audio: AudioSource | list[AudioSource]):
        """Установить следующую музыку"""

        if isinstance(audio, list):
            for i, aud in enumerate(audio):
                self.insert(i, aud)
        else:
            self.insert(0, audio)

    @property
    def latest(self) -> AudioSource | None:
        """Последняя проигранная музыка"""
        return self._latest

    @property
    def current(self) -> AudioSource | None:
        """Текущая музыка"""
        return self._current

    @current.setter
    def current(self, value: AudioSource | None):
        self._latest = self.current or self._latest or value
        self._current = value


class AudioController:
    """
    Контроллер проигрывания музыки.

    Являет собой обёртку над `VoiceClient` для удобного управления воспроизведением.

    Поддерживает следующий функционал:

    - Очередь музыки
    - Автоповтор музыки
    - Управление проигрыванием (play, stop, skip)
    """

    _controllers = {}

    @classmethod
    def get_controller(cls, voice_client: VoiceClient) -> 'AudioController':
        """Получить контроллер для отдельного сервера"""

        cont = cls._controllers.get(voice_client.guild.id)

        # Создать контроллер, если его нету
        if cont is None:
            cont = AudioController(voice_client)
            cls._controllers[voice_client.guild.id] = cont

        return cont

    def __init__(self, voice_client: VoiceClient) -> None:
        self.voice_client = voice_client
        self._loop_running = False
        "Флаг для остановки цикла проигрывания музыки"

    def _play_loop(self, error: any = None) -> None:
        """
        Рекурсивная функция проигрывания музыки.

        Передаётся в аргумент `after` метода `VoiceClient.play`
        """

        # Флаг для остановки цикла
        if not self._loop_running:
            return

        next_audio = self.queue.next()

        # Остановить цикл, если очередь пуста
        if next_audio is None:
            self._loop_running = False
            return

        self._play_music(next_audio)

    def _play_music(self, audio: AudioSource):
        """Проиграть музыку"""

        ffmpeg_options = FFMPEG_OPTIONS.copy()

        # Использовать фильтр для спонсорских сегментов (интеграция SponsorBlock)
        if isinstance(audio, YoutubeVideo):
            ffmpeg_options.setdefault('options', '')
            segments = youtube_utils.get_skip_segments(audio.id)

            if segments is not None:
                opts = youtube_utils.get_ffmpeg_sponsor_filter(segments, audio.duration)
                ffmpeg_options['options'] += ' ' + opts

        self.voice_client.play(
            FFmpegPCMAudio(audio.source_url, **ffmpeg_options),
            after=self._play_loop
        )

    def play(self):
        """Проиграть музыку"""

        self._loop_running = True
        self._play_loop()

    def stop(self):
        """Остановить проигрывание музыки"""

        self._loop_running = False
        self.voice_client.stop()

    def skip(self, count: int = 1):
        """Пропустить музыку"""

        self.queue.skip(count - 1)

        if self.voice_client.is_playing():
            self.voice_client.stop()
        else:
            self.play()

    def play_now(self, audio: AudioSource | list[AudioSource]):
        """Проиграть музыку сразу"""

        self.queue.set_next(audio)

        if self.voice_client.is_playing():
            self.voice_client.stop()
        else:
            self.play()

    @property
    def queue(self) -> AudioQueue:
        """Очередь музыки"""

        return AudioQueue.get_queue(self.voice_client.guild.id)
