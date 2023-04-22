"""
Модуль с командами бота
"""

from datetime import datetime
from yt_dlp import YoutubeDL
from discord.ext.commands import Context, parameter
from settings import bot
from . import utils
from .utils import youtube_utils
from .data import GuildData, langs
from .audio import AudioQueue, AudioController



@bot.command()
async def ping(ctx: Context):
    "Проверить работоспособность бота"

    await ctx.send('Pong!')



@bot.command('echo', aliases=['say', 'bot'])
async def echo(
    ctx,
    *,
    message: str = parameter(description='Сообщение')
):
    "Отправить сообщение от лица бота"

    await ctx.send(message)



@bot.command('connect', aliases=['join', 'j'])
async def connect(ctx: Context) -> bool:
    "Подключиться к голосовому каналу"

    guild = GuildData.get_instance(ctx.guild.id)

    # Выдать ошибку, если пользователь не в голосовом канале
    if ctx.author.voice is None:
        await ctx.send(guild.lang['error.not_in_voice_channel'])
        return False

    # Подключиться к голосовому каналу, если бот не подключён
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    return True



@bot.command('leave', aliases=['disconnect', 'quit', 'q', 'l'])
async def leave(ctx: Context) -> bool:
    "Отключиться от голосового канала"

    # Если бот не в голосовом канале
    if ctx.voice_client is None:
        return False

    await ctx.voice_client.disconnect()
    AudioQueue.get_queue(ctx.guild.id).delete()
    return True



@bot.command('spam', aliases=['flood'])
async def spam(
    ctx: Context,
    count: int = parameter(description='Количество повторов'),
    delay: float = parameter(description='Задержка между повторами'),
    *,
    text: str = parameter(description='Текст для спама')
):
    "Спамить текстом"

    guild = GuildData.get_instance(ctx.guild.id)

    # Валидация аргументов
    if count < 1 or count > 100:
        return await ctx.send(guild.lang['error.args.spam.count'])
    if delay < 0.5 or delay > 60:
        return await ctx.send(guild.lang['error.args.spam.delay'])

    _spam = GuildData.get_instance(ctx.guild.id).create_spam(text, count, delay)

    async for _ in _spam:
        await ctx.send(text)



@bot.command('stopspam', aliases=['switch'])
async def stopspam(
    ctx: Context,
    *,
    code: str = parameter(description='Код для остановки спама. Только жильцы самих недр владеют этим знанием.')
):
    "Остановить спам"

    guild = GuildData.get_instance(ctx.guild.id)
    correct_code = datetime.now().strftime('%M%H')

    if code == correct_code:
        GuildData.get_instance(ctx.guild.id).spam.stop()
    else:
        await ctx.send(guild.lang['error.args.stopspam.code'])



@bot.command('getlink', aliases=['geturl', 'link'])
async def getlink(
    ctx: Context,
    url: str = parameter(description='Ссылка на видео'),
    result_type: str = parameter(default='video', description='Тип результата (video, audio)')
):
    "Получить прямую ссылку на видео/аудио"

    _format = 'bestaudio' if result_type == 'audio' else 'best*[acodec!=none]'
    video = YoutubeDL({'format': _format}).extract_info(url, download=False)

    await ctx.send(video['url'])



@bot.command('play', aliases=['p'])
async def play(
    ctx: Context,
    *,
    url_or_search: str = parameter(default=None, description='Ссылка на видео или поисковый запрос')
):
    """Воспроизвести музыку"""

    # Подключиться к каналу
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    # Если вызвано как алиас команды connect
    if url_or_search is None:
        return

    guild = GuildData.get_instance(ctx.guild.id)

    # Отправить сообщение
    await ctx.send(guild.lang['result.searching'])

    # Начать воспроизведение
    controller = AudioController.get_controller(ctx.voice_client)
    sources = youtube_utils.process_youtube_search(url_or_search)
    controller.play_now(sources)

    # Отправить сообщение
    if len(controller.queue) != 0:
        video = controller.queue[0]
        title = '' if utils.is_url(video.origin_query) else video.url
        await ctx.send(guild.lang['result.video_playing'].format(title))



@bot.command('add', aliases=['a', '+'])
async def add(
    ctx: Context,
    *,
    url_or_search: str = parameter(default=None, description='Ссылка на видео или поисковый запрос')
):
    "Добавить песню в очередь"

    # Подключиться к каналу
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    # Если вызвано как алиас команды connect
    if url_or_search is None:
        return

    guild = GuildData.get_instance(ctx.guild.id)

    # Отправить сообщение
    await ctx.send(guild.lang['result.searching'])

    # Добавить песню в очередь
    sources = youtube_utils.process_youtube_search(url_or_search)
    controller = AudioController.get_controller(ctx.voice_client)
    controller.queue.extend(sources)

    # Отправить сообщение
    # TODO сейчас оно выводит название последнего видео очереди. Если это плейлист, то вывести его название
    if len(controller.queue) != 0:
        video = controller.queue[0]
        title = '' if utils.is_url(video.origin_query) else video.url
        await ctx.send(guild.lang['result.video_added'].format(title))

    # Начать воспроизведение, если не воспроизводится
    if not ctx.voice_client.is_playing():
        controller.play()



@bot.command('skip', aliases=['next', 'nx', 'sk'])
async def skip(
    ctx: Context,
    count: int = parameter(default=1, description='Количество песен для пропуска')
):
    "Пропустить текущую песню"

    guild = GuildData.get_instance(ctx.guild.id)

    # Ошибка, если бот не в голосовом канале
    if ctx.voice_client is None:
        return await ctx.send(guild.lang['error.not_in_voice_channel'])

    # Пропустить песни
    controller = AudioController.get_controller(ctx.voice_client)
    controller.skip(count)

    # Отправить сообщение
    await ctx.send(guild.lang['result.video_skipped'])



@bot.command('stop', aliases=['s'])
async def stop(ctx: Context):
    "Остановить воспроизведение и очистить очередь"

    guild = GuildData.get_instance(ctx.guild.id)

    # Если бот не в голосовом канале
    if not ctx.voice_client.is_playing():
        return await ctx.send(guild.lang['error.not_playing'])

    queue = AudioQueue.get_queue(ctx.guild.id)

    # Остановить replay
    if queue.on_replay:
        queue.on_replay = False

    # Остановить воспроизведение и очистить очередь
    queue.clear()
    ctx.voice_client.stop()

    # Отправить сообщение
    await ctx.send(guild.lang['result.video_stopped'])



@bot.command('pause', aliases=['wait'])
async def pause(ctx: Context):
    "Поставить на паузу"

    guild = GuildData.get_instance(ctx.guild.id)

    # Ошибка, если бот не в голосовом канале
    if ctx.voice_client is None:
        return await ctx.send(guild.lang['error.not_in_voice_channel'])
    # Ошибка, если бот и так на паузе
    if ctx.voice_client.is_paused():
        return await ctx.send(guild.lang['error.already_paused'])
    # Ошибка, если воспроизведение остановлено
    if not ctx.voice_client.is_playing():
        return await ctx.send(guild.lang['error.already_stopped'])

    ctx.voice_client.pause()
    await ctx.send(guild.lang['result.video_paused'])



@bot.command('resume', aliases=['continue', 'unpause', 'res'])
async def resume(ctx: Context):
    "Продолжить воспроизведение"

    guild = GuildData.get_instance(ctx.guild.id)

    # Ошибка, если бот не в голосовом канале
    if ctx.voice_client is None:
        return await ctx.send(guild.lang['error.not_in_voice_channel'])
    # Ошибка, если бот и так играет музыку
    if ctx.voice_client.is_playing():
        return await ctx.send(guild.lang['error.already_playing'])
    # Ошибка, если бот не на паузе
    if not ctx.voice_client.is_paused():
        return await ctx.send(guild.lang['error.queue_empty'])

    ctx.voice_client.resume()
    await ctx.send(guild.lang['result.video_resumed'])



@bot.command('replay', aliases=['repeat', 'loop', 'repl', 'rep', 'rp'])
async def replay(
    ctx: Context,
    *,
    url_or_search: str = parameter(default=None, description='Ссылка на видео или поисковый запрос')
):
    "Поставить на повтор"

    guild = GuildData.get_instance(ctx.guild.id)

    # Подключиться к каналу
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    # Если команда вызвана без параметров, то просто включить/выключить повтор текущей музыки
    if url_or_search is None:
        if guild.queue.on_replay:
            guild.queue.on_replay = False
            await ctx.send(guild.lang['result.replay_disabled'])
        else:
            guild.queue.on_replay = True
            await ctx.send(guild.lang['result.replay_enabled'])
        return

    # Отправить сообщение
    await ctx.send(guild.lang['result.searching'])

    # Начать автовоспроизведение
    sources = youtube_utils.process_youtube_search(url_or_search)
    controller = AudioController.get_controller(ctx.voice_client)
    controller.queue.on_replay = True
    controller.play_now(sources)

    # Отправить сообщение
    await ctx.send(guild.lang['result.replay_enabled'])



@bot.command('queue', aliases=['list'])
async def queue(ctx: Context):
    "Показать очередь"

    guild = GuildData.get_instance(ctx.guild.id)

    # Ошибка, если очередь пуста
    if len(guild.queue) == 0 and guild.queue._current is None:
        return await ctx.send(guild.lang['result.queue.empty'])

    # Отправить сообщение
    await ctx.send(guild.lang['result.queue'].format(
        '\n'.join(
            f'{i + 1}. {video.title}' for i, video in enumerate(guild.queue.full_queue)
        ) or guild.lang['text.empty']
    ))



@bot.command()
async def clear(ctx: Context):
    "Очистить очередь, не останавливая воспроизведение текущей музыки"

    guild = GuildData.get_instance(ctx.guild.id)
    queue_len = len(guild.queue)

    # Ошибка, если очередь пуста
    if queue_len == 0:
        return await ctx.send(guild.lang['error.queue_empty'])

    queue.clear()

    # Отправить сообщение
    await ctx.send(guild.lang['result.queue_cleared'].format(queue_len))



@bot.command('playlast', aliases=['last', 'latest'])
async def playlast(ctx: Context):
    "Воспроизвести последнюю музыку"

    guild = GuildData.get_instance(ctx.guild.id)
    controller = AudioController.get_controller(ctx.voice_client)

    # Ошибка, если последняя музыка не найдена
    if controller.queue.latest is None:
        return await ctx.send(guild.lang['error.no_last_video'])

    controller.queue.set_next(controller.queue.latest)

    # Воспроизвести последнюю музыку
    controller.skip()

    # Отправить сообщение
    await ctx.send(guild.lang['result.playing_last'])



@bot.command('language', aliases=['lang'])
async def language(
    ctx: Context,
    lang_code: str = parameter(default=None, description='Язык')
):
    "Установить язык бота"

    guild = GuildData.get_instance(ctx.guild.id)

    # Отобразить помощь, если язык не указан
    if lang_code is None:
        return await ctx.send(guild.lang['result.language_help'].format(guild.lang_code))

    # Ошибка, если язык не найден
    if lang_code not in langs:
        return await ctx.send(guild.lang['error.language_not_found'])

    guild.lang_code = lang_code

    # Отправить сообщение
    await ctx.send(guild.lang['result.language_set'])



@bot.command('languages', aliases=['langs'])
async def languages(ctx: Context):
    "Показать список доступных языков"

    guild = GuildData.get_instance(ctx.guild.id)
    await ctx.send(guild.lang['result.languages'])
