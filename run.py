"""
Главный файл бота
"""

import os
import logging
import bot.commands as _

from settings import bot
from bot.data import GuildData, AudioQueue
from bot.utils.discord_utils import is_users_in_channel, get_bot_channel

logger = logging.getLogger('bot')



@bot.event
async def on_ready():
    'Выполняется при запуске бота'
    logger.info('Bot is ready!')



@bot.event
async def on_voice_state_update(member, before, after):
    """
    Ливнуть с канала, если в нём никого не осталось,\n
    или перейти в канал пользователя, если он сменил канал, и бот остался один.
    """

    if member.bot:
        return

    ch = get_bot_channel(bot, before, after)

    # Игнорировать, если это не касается канала бота
    if ch is None:
        return

    # Игнорировать, если в канале есть пользователи
    if is_users_in_channel(ch):
        return


    # Перейти в канал пользователя, если он его сменил
    if after is not None and after.channel is not None:
        if after.channel.id == ch.id:
            return
        if GuildData.get_instance(ch.guild.id).make_move():
            await ch.guild.voice_client.move_to(after.channel)

    # Ливнуть с канала
    else:
        #Защита от случайного отключения человека от канала
        #Если пользователь в течении 750мс не вернётся в канал, то бот отключится
        #await sleep(0.75)
        #if not is_users_in_channel(ch):
        await ch.guild.voice_client.disconnect()
        AudioQueue.del_queue(ch.guild.id)


bot.run(os.getenv('BOT_TOKEN'))
