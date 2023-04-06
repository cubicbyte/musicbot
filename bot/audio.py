from discord import VoiceClient, FFmpegPCMAudio
from discord.ext.commands import Bot
from bot.schemas import AudioSource
from bot.utils import is_users_in_channel
from settings import FFMPEG_OPTIONS



class AudioQueue(list):
    _global_queue: dict[str, 'AudioQueue'] = {}


    def __init__(self, guild_id: int) -> None:
        super().__init__()

        self.guild_id = guild_id
        self.on_replay = False


    def get(guild_id: int) -> 'AudioQueue':
        "Получить очередь для отдельного сервера"

        _guild_id = str(guild_id)
        queue = AudioQueue._global_queue.get(_guild_id)

        # Создать очередь, если её нету
        if queue is None:
            queue = AudioQueue(guild_id)
            AudioQueue._global_queue[_guild_id] = queue

        return queue


    def unregister(self):
        "Удалить очередь из глобального списка для очистки памяти"

        _guild_id = str(self.guild_id)

        if _guild_id in AudioQueue._global_queue:
            del AudioQueue._global_queue[_guild_id]


    @property
    def current(self) -> AudioSource | None:
        "Текущая музыка"

        if len(self) == 0:
            return None
        else:
            return self[0]


    @current.setter
    def current(self, audio: AudioSource):
        if len(self) == 0:
            self.append(audio)
        else:
            self[0] = audio


    def play_next_music(self, bot: Bot, vc: VoiceClient, is_after: bool = False):
        "Проиграть следующую песню из очереди"

        # Удалить старую музыку из очереди
        # А так же ливнуть с канала, если в нём никого не осталось
        if is_after:
            if not is_users_in_channel(vc.channel):
                vc.disconnect()
                self.unregister()
                return
            self.pop(0)

        # Убрать паузу
        if vc.is_paused():
            vc.resume()

        # Если очередь пуста, то отмена
        if self.current is None:
            return

        vc.play(
            FFmpegPCMAudio(self.current.source_url, **FFMPEG_OPTIONS),
            after=lambda _: self.play_next_music(bot, vc, is_after=True)
        )


    def skip(self, bot: Bot, vc: VoiceClient, count: int = 1):
        "Пропустить музыку"

        # Отключить автовоспроизведение
        if self.on_replay:
            self.on_replay = False

        for _ in range(count - 1):
            self.pop(0)

        if vc.is_playing():
            vc.stop()
        else:
            self.play_next_music(bot, vc)


    def clear(self) -> None:
        "Очистить очередь"

        super().clear()
        self.current = None
