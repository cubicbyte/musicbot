from discord import VoiceClient, FFmpegPCMAudio
from discord.ext.commands import Bot
from bot.schemas import AudioSource
from config import FFMPEG_OPTIONS



class AudioQueue(list):
    _global_queue: dict[str, 'AudioQueue'] = {}


    def __init__(self, guild_id: int) -> None:
        super().__init__()

        self.guild_id = guild_id
        self.on_replay = False
        self.current: AudioSource | None = None # TODO убрать current но сделать его @property


    def get(guild_id: int) -> 'AudioQueue':
        "Получить очередь для отдельного сервера"

        _guild_id = str(guild_id)
        queue = AudioQueue._global_queue.get(_guild_id)

        # Создать очередь, если её нету
        if queue is None:
            queue = AudioQueue(guild_id)
            AudioQueue._global_queue[_guild_id] = queue

        return queue


    def __del__(self):
        "Удалить очередь из глобального списка для очистки памяти"

        _guild_id = str(self.guild_id)

        if _guild_id in AudioQueue._global_queue:
            del AudioQueue._global_queue[_guild_id]


    def set_current(self, video: AudioSource):
        "Установить текущую музыку"

        if self.on_replay:
            self.current = video
        elif len(self) == 0:
            self.append(video)
        else:
            self[0] = video


    def get_next(self) -> AudioSource | None:
        "Вернуть следующую песню из очереди"

        # Если включен режим повтора, то возвращаем текущую песню и не удаляем ее из очереди
        if not self.on_replay or self.current is None:
            self.current = self.pop(0) if len(self) != 0 else None

        return self.current


    def play_next_music(self, bot: Bot, vc: VoiceClient):
        "Проиграть следующую песню из очереди"

        next_music = self.get_next()

        # Убрать паузу
        if vc.is_paused():
            vc.resume()

        if next_music is None:
            return

        vc.play(
            FFmpegPCMAudio(next_music.source_url, **FFMPEG_OPTIONS),
            after=lambda _: self.play_next_music(bot, vc)
        )


    def skip(self, bot: Bot, vc: VoiceClient, count: int = 1):
        "Пропустить музыку"

        # Отключить автовоспроизведение
        if self.on_replay:
            self.on_replay = False

        for _ in range(count - 1):
            self.get_next()

        if vc.is_playing():
            vc.stop()
        else:
            self.play_next_music(bot, vc)


    def clear(self) -> None:
        "Очистить очередь"

        super().clear()
        self.current = None
