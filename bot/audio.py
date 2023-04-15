"""
Модуль для работы с музыкой
"""

from discord import VoiceClient, FFmpegPCMAudio
from .schemas import AudioSource
from settings import FFMPEG_OPTIONS



class AudioQueue(list):
    _global_queue: dict[str, 'AudioQueue'] = {}


    @classmethod
    def get_queue(cls, guild_id: int) -> 'AudioQueue':
        "Получить очередь для отдельного сервера"

        _guild_id = str(guild_id)
        queue = cls._global_queue.get(_guild_id)

        # Создать очередь, если её нету
        if queue is None:
            queue = AudioQueue(guild_id)
            cls._global_queue[_guild_id] = queue

        return queue


    @classmethod
    def del_queue(cls, guild_id: int):
        "Удалить очередь из глобального списка для очистки памяти"

        _guild_id = str(guild_id)

        if _guild_id in cls._global_queue:
            del cls._global_queue[_guild_id]


    def __init__(self, guild_id: int) -> None:
        self.guild_id = guild_id
        "ID сервера"
        self.on_replay = False
        "Автоповтор музыки"
        self._current = None
        "Текущая музыка"


    @property
    def full_queue(self) -> list[AudioSource]:
        "Очередь с учётом текущей музыки"

        if self.current is None:
            return self.copy()

        return [self.current, *self]


    def delete(self):
        "Удалить очередь из глобального списка для очистки памяти"
        AudioQueue.del_queue(self.guild_id)


    def skip(self, count: int = 1):
        "Пропустить музыку"

        for _ in range(count):
            if len(self) == 0:
                self._current = None
                break

            self._current = self.pop(0)


    def next(self) -> AudioSource | None:
        "Следующая музыка"

        if not self.on_replay:
            self.skip()

        return self.current


    @property
    def current(self) -> AudioSource | None:
        "Текущая музыка"

        if self._current is None and len(self) != 0:
            self._current = self.pop(0)

        return self._current


    @current.setter
    def current(self, value: AudioSource | None):
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
        "Получить контроллер для отдельного сервера"

        cont = cls._controllers.get(voice_client.guild.id)

        # Создать контроллер, если его нету
        if cont is None:
            cont = AudioController(voice_client)
            cls._controllers[voice_client.guild.id] = cont

        return cont


    def __init__(self, voice_client: VoiceClient):
        self.voice_client = voice_client
        self._loop_running = False
        "Флаг для остановки цикла проигрывания музыки"


    def _play_loop(self, error):
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
        "Проиграть музыку"

        self.voice_client.play(
            FFmpegPCMAudio(audio.source_url, **FFMPEG_OPTIONS),
            after=self._play_loop
        )


    def play(self):
        "Проиграть музыку"

        self._loop_running = True
        self._play_loop(error=None)


    def stop(self):
        "Остановить проигрывание музыки"

        self._loop_running = False
        self.voice_client.stop()


    def skip(self, count: int = 1):
        "Пропустить музыку"

        self.queue.skip(count)
        self.stop()
        self.play()


    @property
    def queue(self) -> AudioQueue:
        "Очередь музыки"

        return AudioQueue.get_queue(self.voice_client.guild.id)
