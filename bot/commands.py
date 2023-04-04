from datetime import datetime
from yt_dlp import YoutubeDL
from discord.ext.commands import Context, parameter
from bot import utils
from bot.utils.youtube import search_youtube
from bot.data import GuildData, LanguageManager
from bot.audio import AudioQueue
from bot.schemas import YoutubeVideo
from settings import bot
from config import DEFAULT_LANG

_lang = LanguageManager.get_lang(DEFAULT_LANG)



def add_yt_result_to_queue(ydl_res: dict[str, any], queue: AudioQueue):
    "Добавить видео или плейлист с Youtube в очередь"

    # Если это плейлист, то добавляем все его видео в очередь
    if ydl_res.get('_type') == 'playlist':
        for video in ydl_res['entries']:
            queue.append(YoutubeVideo.from_ydl(video))

    # Если это видео, то добавляем его в очередь
    else:
        queue.append(YoutubeVideo.from_ydl(ydl_res))



@bot.command()
async def ping(ctx: Context):
    "Проверить работоспособность бота"

    await ctx.send(_lang['result.ping'])



@bot.command('echo', aliases=['say'])
async def echo(ctx, *, message: str):
    "Отправить сообщение от лица бота"

    await ctx.send(message)



@bot.command('connect', aliases=['join', 'j'])
async def connect(ctx: Context) -> bool:
    "Подключиться к голосовому каналу"

    # Выдать ошибку, если пользователь не в голосовом канале
    if ctx.author.voice is None:
        await ctx.send(_lang['error.not_in_voice_channel'])
        return False

    await ctx.author.voice.channel.connect()
    return True



@bot.command('leave', aliases=['disconnect', 'quit', 'q', 'l'])
async def leave(ctx: Context) -> bool:
    "Отключиться от голосового канала"

    # Если бот не в голосовом канале
    if ctx.voice_client is None:
        return False

    await ctx.voice_client.disconnect()
    AudioQueue.get(ctx.guild.id).unregister()
    return True



@bot.command()
async def spam(
    ctx: Context,
    count: int = parameter(description='Количество повторов'),
    delay: float = parameter(description='Задержка между повторами'),
    *,
    text: str = parameter(description='Текст для спама')
):
    "Спамить текстом"

    # Валидация аргументов
    if count < 1 or count > 100:
        return await ctx.send(_lang['error.args.spam.count'])
    if delay < 0.5 or delay > 60:
        return await ctx.send(_lang['error.args.spam.delay'])

    _spam = GuildData.get(ctx.guild.id).create_spam(text, count, delay)
    async for _ in _spam:
        await ctx.send(text)



@bot.command()
async def switch(
    ctx: Context,
    *,
    code: str = parameter(description='Код для остановки спама. Только жильцы самих недр владеют этим знанием.')
):
    "Остановить спам"

    correct_code = datetime.now().strftime('%M%H')

    if code == correct_code:
        GuildData.get(ctx.guild.id).spam.stop()



@bot.command('getlink', aliases=['link'])
async def getlink(
    ctx: Context,
    url: str = parameter(description='Ссылка на видео или поисковый запрос'),
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

    # Убрать паузу
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()

    # Добавить видео в очередь
    queue = AudioQueue.get(ctx.guild.id)
    ydl_res = search_youtube(url_or_search)
    add_yt_result_to_queue(ydl_res, queue)

    # Сразу начать воспроизведение
    queue.skip(bot, ctx.voice_client)

    # Отправить сообщение
    video = queue.current
    title = '' if utils.is_url(url_or_search) else video.origin_query
    await ctx.send(_lang['result.video_playing'].format(title))



@bot.command('add', aliases=['a'])
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

    # Добавить видео в очередь
    queue = AudioQueue.get(ctx.guild.id)
    ydl_res = search_youtube(url_or_search)
    add_yt_result_to_queue(ydl_res, queue)

    # Начать воспроизведение, если очередь была пуста
    if not ctx.voice_client.is_playing():
        queue.play_next_music(bot, ctx.voice_client)

    # Отправить сообщение
    # TODO сейчас оно выводит последнее видео очереди. Если это плейлист, то вывести его название
    video = queue[-1] if len(queue) != 0 else queue.current
    title = '' if utils.is_url(url_or_search) else video.origin_query
    await ctx.send(_lang['result.video_added'].format(title))



@bot.command('skip', aliases=['next'])
async def skip(
    ctx: Context,
    count: int = parameter(default=1, description='Количество песен для пропуска')
):
    "Пропустить текущую песню"

    # Ошибка, если бот не в голосовом канале
    if ctx.voice_client is None:
        return await ctx.send(_lang['error.not_in_voice_channel'])

    # Пропустить песни
    queue = AudioQueue.get(ctx.guild.id)
    queue.skip(bot, ctx.voice_client, count)

    # Отправить сообщение
    await ctx.send(_lang['result.video_skipped'])



@bot.command('stop', aliases=['s'])
async def stop(ctx: Context):
    "Остановить воспроизведение и очистить очередь"

    queue = AudioQueue.get(ctx.guild.id)

    # Если бот не в голосовом канале
    if not ctx.voice_client.is_playing():
        return await ctx.send(_lang['error.not_playing'])

    # Остановить replay
    if queue.on_replay:
        queue.on_replay = False

    # Остановить воспроизведение и очистить очередь
    queue.clear()
    ctx.voice_client.stop()

    # Отправить сообщение
    await ctx.send(_lang['result.video_stopped'])



@bot.command('pause', aliases=['wait'])
async def pause(ctx: Context):
    "Поставить на паузу"

    # Ошибка, если бот не в голосовом канале
    if ctx.voice_client is None:
        return await ctx.send(_lang['error.not_in_voice_channel'])
    # Ошибка, если бот и так на паузе
    if ctx.voice_client.is_paused():
        return await ctx.send(_lang['error.already_paused'])
    # Ошибка, если воспроизведение остановлено
    if not ctx.voice_client.is_playing():
        return await ctx.send(_lang['error.already_stopped'])

    ctx.voice_client.pause()
    await ctx.send(_lang['result.video_paused'])



@bot.command()
async def resume(ctx: Context):
    "Продолжить воспроизведение"

    # Ошибка, если бот не в голосовом канале
    if ctx.voice_client is None:
        return await ctx.send(_lang['error.not_in_voice_channel'])
    # Ошибка, если бот и так играет музыку
    if ctx.voice_client.is_playing():
        return await ctx.send(_lang['error.already_playing'])
    # Ошибка, если бот не на паузе
    if not ctx.voice_client.is_paused():
        return await ctx.send(_lang['error.queue_empty'])

    ctx.voice_client.resume()
    await ctx.send(_lang['result.video_resumed'])



@bot.command()
async def replay(
    ctx: Context,
    *,
    url_or_search: str = parameter(default=None, description='Ссылка на видео или поисковый запрос')
):
    "Поставить на повтор"

    queue = AudioQueue.get(ctx.guild.id)

    # Подключиться к каналу
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    # Если команда вызвана без параметров, то просто включить/выключить повтор текущей музыки
    if url_or_search is None:
        if queue.on_replay:
            queue.on_replay = False
            #queue.next() TODO remove this if neccessary
            return await ctx.send(_lang['result.replay_disabled'])
        else:
            queue.on_replay = True
            return await ctx.send(_lang['result.replay_enabled'])

    # Включить повтор введенной музыки
    ydl_res = search_youtube(url_or_search)
    # Ошибка, если это плейлист
    if ydl_res.get('_type') == 'playlist':
        return await ctx.send(_lang['error.replay_playlist_not_supported'])
    queue.on_replay = True
    queue.set_current(YoutubeVideo.from_ydl(ydl_res))

    # Сразу начать воспроизведение
    queue.skip(bot, ctx.voice_client)

    # Отправить сообщение
    await ctx.send(_lang['result.replay_enabled'])



@bot.command()
async def queue(ctx: Context):
    "Показать очередь"

    queue = AudioQueue.get(ctx.guild.id)

    # Ошибка, если очередь пуста
    if len(queue) == 0 and queue.current is None:
        return await ctx.send(_lang['result.queue.empty'])

    # Отправить сообщение
    await ctx.send(_lang['result.queue'].format(
        '\n'.join(
            f'{i + 1}. {video.title}' for i, video in enumerate(queue)
        ) or _lang['text.empty']
    ))
