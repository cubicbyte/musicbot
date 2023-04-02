import ast
import urllib
import urllib.parse
from discord import VoiceState, VoiceChannel
from discord.ext.commands import Bot


def unescape_string(escaped_string: str) -> str:
    "Преобразовать строку с экранированными символами (e.g. \\n) в нормальную строку"
    return ast.literal_eval(f'"{escaped_string}"')


def is_url(string: str) -> bool:
    "Проверить, является ли строка ссылкой"
    try:
        r = urllib.parse.urlparse(string)
        return all([r.scheme, r.netloc])
    except ValueError:
        return False


def is_users_in_channel(channel: VoiceChannel):
    "Проверить, есть ли в голосовом канале пользователи. Боты не учитываются."
    for member in channel.members:
        if not member.bot:
            return True
    return False


def is_connected(bot: Bot, channel: VoiceChannel):
    "Проверить, подключён ли бот к голосовому каналу"
    for member in channel.members:
        if member.id == bot.user.id:
            return True
    return False


def get_bot_channel(bot: Bot, *states: VoiceState | None) -> VoiceChannel | None:
    "Получить голосовой канал, в котором находится бот"
    for state in states:
        if state is None or state.channel is None:
            continue
        if is_connected(bot, state.channel):
            return state.channel
    return None
