"""
Module for bot commands
"""

import os

from datetime import datetime
from yt_dlp import YoutubeDL
from discord.ext.commands import Context, parameter

from settings import bot
from bot import utils, youtube
from bot.schemas import YoutubeVideo
from bot.data import GuildData, langs
from bot.audio import AudioQueue, AudioController


@bot.command()
async def ping(ctx: Context):
    """Check bot availability"""

    await ctx.send('Pong!')


@bot.command('echo', aliases=['say', 'bot'])
async def echo(
    ctx,
    *,
    message: str = parameter(description='Сообщение')
):
    """Send message on behalf of bot"""

    await ctx.send(message)


@bot.command('connect', aliases=['join', 'j'])
async def connect(ctx: Context) -> bool:
    """Connect to voice channel"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Throw error if user is not in voice channel
    if ctx.author.voice is None:
        await ctx.send(guild.lang['error.not_in_voice_channel'])
        return False

    # Connect to voice channel if bot is not connected
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    return True


@bot.command('leave', aliases=['disconnect', 'quit', 'q', 'l'])
async def leave(ctx: Context) -> bool:
    """Disconnect from voice channel"""

    # If bot is not in voice channel, do nothing
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
    """Spam text"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Validate arguments
    if count < 1 or count > 100:
        return await ctx.send(guild.lang['error.args.spam_count'])
    if delay < 0.5 or delay > 60:
        return await ctx.send(guild.lang['error.args.spam_delay'])

    _spam = GuildData.get_instance(ctx.guild.id).create_spam(text, count, delay)

    async for _ in _spam:
        await ctx.send(text)


@bot.command('stopspam', aliases=['switch'])
async def stopspam(
        ctx: Context,
        *,
        code: str = parameter(
            description='Код для остановки спама. Только жильцы самих недр владеют этим знанием.'
        )
):
    """Stop spam"""

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
    """Get direct link to video/audio"""

    _format = 'bestaudio' if result_type == 'audio' else 'best*[acodec!=none]'
    video = YoutubeDL({'format': _format}).extract_info(url, download=False)

    await ctx.send(video['url'])


@bot.command('play', aliases=['p'])
async def play(
        ctx: Context,
        *,
        url_or_search: str = parameter(default=None, description='Ссылка на видео или поисковый запрос')
):
    """Play video or audio"""

    # Connect to voice channel
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    # If called as alias of connect command, connect and return
    if url_or_search is None:
        return

    guild = GuildData.get_instance(ctx.guild.id)

    # Send callback message
    await ctx.send(guild.lang['result.searching'])

    # Start playing
    controller = AudioController.get_controller(ctx.voice_client)
    sources = youtube.process_youtube_search(url_or_search)
    controller.play_audio(sources)

    # Send another callback message
    video = controller.queue.current
    if video is not None:
        title = '' if utils.is_url(video.origin_query) else video.url
        await ctx.send(guild.lang['result.video_playing'].format(title))


@bot.command('add', aliases=['a', '+'])
async def add(
        ctx: Context,
        *,
        url_or_search: str = parameter(default=None, description='Ссылка на видео или поисковый запрос')
):
    """Add video or audio to queue"""

    # Connect to voice channel
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    # If called as alias of connect command, connect and return
    if url_or_search is None:
        return

    guild = GuildData.get_instance(ctx.guild.id)

    # Send callback message
    await ctx.send(guild.lang['result.searching'])

    # Add video to queue
    sources = youtube.process_youtube_search(url_or_search)
    controller = AudioController.get_controller(ctx.voice_client)
    controller.queue.extend(sources)

    # Send another callback message
    if len(controller.queue) != 0:
        video = controller.queue[0]
        title = '' if utils.is_url(video.origin_query) else video.url
        await ctx.send(guild.lang['result.video_added'].format(title))

    # Start playing if queue was empty
    if not ctx.voice_client.is_playing():
        controller.start()


@bot.command('skip', aliases=['next', 'nx', 'sk'])
async def skip(
        ctx: Context,
        count: int = parameter(default=1, description='Количество песен для пропуска')
):
    """Skip current video or audio"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Error if bot is not in voice channel
    if ctx.voice_client is None:
        return await ctx.send(guild.lang['error.not_in_voice_channel'])

    # Skip current audio
    controller = AudioController.get_controller(ctx.voice_client)
    controller.skip(count)

    # Send message
    await ctx.send(guild.lang['result.video_skipped'])


@bot.command('stop', aliases=['s'])
async def stop(ctx: Context):
    """Stop playing and clear queue"""

    guild = GuildData.get_instance(ctx.guild.id)

    # If already stopped, send error
    if not ctx.voice_client.is_playing():
        return await ctx.send(guild.lang['error.not_playing'])

    _queue = AudioQueue.get_queue(ctx.guild.id)

    # Stop replay
    if _queue.on_replay:
        _queue.on_replay = False

    # Stop playing and clear queue
    _queue.clear()
    ctx.voice_client.stop()

    # Send message
    await ctx.send(guild.lang['result.video_stopped'])


@bot.command('pause', aliases=['wait'])
async def pause(ctx: Context):
    """Pause playing"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Error if bot is not in voice channel
    if ctx.voice_client is None:
        return await ctx.send(guild.lang['error.not_in_voice_channel'])
    # Error if bot is already paused
    if ctx.voice_client.is_paused():
        return await ctx.send(guild.lang['error.already_paused'])
    # Error if bot is not playing
    if not ctx.voice_client.is_playing():
        return await ctx.send(guild.lang['error.already_stopped'])

    ctx.voice_client.pause()
    await ctx.send(guild.lang['result.video_paused'])


@bot.command('resume', aliases=['continue', 'unpause', 'res'])
async def resume(ctx: Context):
    """Continue playing"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Error if bot is not in voice channel
    if ctx.voice_client is None:
        return await ctx.send(guild.lang['error.not_in_voice_channel'])
    # Error if bot is already playing
    if ctx.voice_client.is_playing():
        return await ctx.send(guild.lang['error.already_playing'])
    # Error if bot is not paused
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
    """Enable auto replay"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Connect to voice channel
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    # If no arguments, just enable/disable replay
    if url_or_search is None:
        if guild.queue.on_replay:
            guild.queue.on_replay = False
            await ctx.send(guild.lang['result.replay_disabled'])
        else:
            guild.queue.on_replay = True
            await ctx.send(guild.lang['result.replay_enabled'])
        return

    # Send callback message
    await ctx.send(guild.lang['result.searching'])

    # Start auto replay
    sources = youtube.process_youtube_search(url_or_search)
    controller = AudioController.get_controller(ctx.voice_client)
    controller.queue.on_replay = True
    controller.play_audio(sources)

    # Send another callback message
    await ctx.send(guild.lang['result.replay_enabled'])


@bot.command('queue', aliases=['list'])
async def queue(ctx: Context):
    """Show queue"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Error if queue is empty
    if len(guild.queue) == 0 and guild.queue.current is None:
        return await ctx.send(guild.lang['result.queue_empty'])

    # Send message
    await ctx.send(guild.lang['result.queue'].format(
        '\n'.join(
            f'{i + 1}. {video.title}' for i, video in enumerate(guild.queue.full_queue)
        ) or guild.lang['text.empty']
    ))


@bot.command()
async def clear(ctx: Context):
    """Clear queue without stopping current audio"""

    guild = GuildData.get_instance(ctx.guild.id)
    queue_len = len(guild.queue)

    # Error if queue is empty
    if queue_len == 0:
        return await ctx.send(guild.lang['error.queue_empty'])

    queue.clear()

    # Send message
    await ctx.send(guild.lang['result.queue_cleared'].format(queue_len))


@bot.command('playlast', aliases=['last', 'latest'])
async def playlast(ctx: Context):
    """Play last audio"""

    guild = GuildData.get_instance(ctx.guild.id)
    controller = AudioController.get_controller(ctx.voice_client)

    # Error if last audio is not found
    if controller.queue.latest is None:
        return await ctx.send(guild.lang['error.no_last_video'])

    controller.queue.set_next(controller.queue.latest)

    # Play last audio
    controller.skip()

    # Send message
    await ctx.send(guild.lang['result.playing_last'])


@bot.command('language', aliases=['lang'])
async def language(
        ctx: Context,
        lang_code: str = parameter(default=None, description='Язык')
):
    """Set bot language"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Show help if no arguments
    if lang_code is None:
        return await ctx.send(guild.lang['result.language_help'].format(guild.lang_code))

    # Error if language is not found
    if lang_code not in langs:
        return await ctx.send(guild.lang['error.language_not_found'])

    guild.lang_code = lang_code

    # Send message
    await ctx.send(guild.lang['result.language_set'])


@bot.command('languages', aliases=['langs'])
async def languages(ctx: Context):
    """Show available languages"""

    guild = GuildData.get_instance(ctx.guild.id)
    await ctx.send(guild.lang['result.languages'])


@bot.command('save', aliases=['savevideo', 'savevid', 'savecurrent', 'savecur'])
async def save(
        ctx: Context,
        name: str = parameter(description='Код-название видео (без пробелов)'),
        *,
        url_or_search: str = parameter(
            default=None,
            description='Ссылка на видео или поисковый запрос',
            displayed_default='текущее видео'
        )
):
    """Save video"""

    guild = GuildData.get_instance(ctx.guild.id)

    # Error, if limit is reached
    if len(guild.get_yt_saves()) >= int(os.getenv('SAVES_LIMIT')):
        return await ctx.send(guild.lang['error.saves_limit'])

    # Save video by url or search query
    if url_or_search is not None:
        videos = youtube.process_youtube_search(url_or_search)

        guild.save_yt_video(videos[0], name)
        return await ctx.send(guild.lang['result.video_saved'].format(name))

    # Save current video
    else:
        # Error, if no current video
        if guild.queue.current is None:
            return await ctx.send(guild.lang['error.no_current_video'])

        # Error, if current video is not youtube video
        if not isinstance(guild.queue.current, YoutubeVideo):
            return await ctx.send(guild.lang['error.not_youtube_video'])

        guild.save_yt_video(guild.queue.current, name)
        await ctx.send(guild.lang['result.video_saved'].format(name))


@bot.command('saves', aliases=['saved', 'getsaves', 'savedvideos', 'savedvids'])
async def saves(ctx: Context):
    """Show saved videos"""

    guild = GuildData.get_instance(ctx.guild.id)
    _saves = guild.get_yt_saves()

    # Send message
    await ctx.send(guild.lang['result.saved_videos'].format(
        '\n'.join(
            f'**{name}**: {video.title}' for name, video in _saves.items()
        ) or guild.lang['text.empty']
    ))


@bot.command('clearsaves', aliases=['clearsave', 'clearsaved',
                                    'clearsavedvideos', 'clearsavedvids'])
async def clearsaves(ctx: Context):
    """Clear saved videos list"""

    guild = GuildData.get_instance(ctx.guild.id)
    saves_len = len(guild.get_yt_saves())

    guild.clear_yt_saves()

    # Send message
    await ctx.send(guild.lang['result.saved_videos_cleared'].format(saves_len))


@bot.command('delsave', aliases=['unsave', 'remsave', 'deletevideo',
                                 'deletevid', 'deletesave', 'deletesaved',
                                 'deletesavedvideo', 'deletesavedvid'])
async def delsave(
        ctx: Context,
        name: str = parameter(description='Код-название видео (без пробелов)')
):
    """Delete saved video"""

    guild = GuildData.get_instance(ctx.guild.id)
    _saves = guild.get_yt_saves()

    # Error, if video not found
    if name not in _saves:
        return await ctx.send(guild.lang['error.video_not_found'])

    guild.delete_saved_yt_video(name)

    # Send message
    await ctx.send(guild.lang['result.video_deleted'].format(name))


@bot.command('playsaved', aliases=['playsave', 'ps'])
async def playsaved(
        ctx: Context,
        name: str = parameter(description='Код-название видео (без пробелов)')
):
    """Play saved video"""

    # Connect to voice channel
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    guild = GuildData.get_instance(ctx.guild.id)
    _saves = guild.get_yt_saves()

    # Error, if video not found
    if name not in _saves:
        return await ctx.send(guild.lang['error.video_not_found'])

    # Start playing
    video = _saves[name]
    controller = AudioController.get_controller(ctx.voice_client)
    controller.play_audio(video)

    # Send message
    await ctx.send(guild.lang['result.video_playing'].format(video.title))


@bot.command('replaysaved', aliases=['replaysave', 'rs'])
async def replaysaved(
        ctx: Context,
        name: str = parameter(description='Код-название видео (без пробелов)')
):
    """Enable auto replay for saved video"""

    # Connect to voice channel
    if ctx.voice_client is None:
        if not await connect(ctx):
            return

    guild = GuildData.get_instance(ctx.guild.id)
    _saves = guild.get_yt_saves()

    # Error, if video not found
    if name not in _saves:
        return await ctx.send(guild.lang['error.video_not_found'])

    # Start auto replay
    video = _saves[name]
    controller = AudioController.get_controller(ctx.voice_client)
    controller.queue.on_replay = True
    controller.play_audio(video)

    # Send message
    await ctx.send(guild.lang['result.video_playing'].format(video.title))
