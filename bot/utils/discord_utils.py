"""
Модуль для работы с Discord API
"""

from discord import VoiceState, VoiceChannel, VoiceClient, User
from discord.ext.commands import Bot



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



def is_user_in_bot_channel(voice_client: VoiceClient, user: User) -> bool:
    "Проверить, находится ли пользователь в голосовом канале бота"

    if voice_client is None or user.voice is None:
        return False

    return user.voice.channel.id == voice_client.channel.id
