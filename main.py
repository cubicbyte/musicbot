import logging
from bot.data import GuildData, LanguageManager, AudioQueue
from config import BOT_TOKEN, LANGS_DIR
from settings import bot
from bot.utils import is_users_in_channel, get_bot_channel

logger = logging.getLogger('bot')
LanguageManager.load(LANGS_DIR)

# Импорт только здесь потому, что модуль ссылается на LanguageManager, который должен быть загружен первее.
from bot import commands



@bot.event
async def on_ready():
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
        if GuildData.get(ch.guild.id).make_move():
            await ch.guild.voice_client.move_to(after.channel)

    # Ливнуть с канала
    else:
        #Защита от случайного отключения человека от канала
        #Если пользователь в течении 750мс не вернётся в канал, то бот отключится
        #await sleep(0.75)
        #if not is_users_in_channel(ch):
        await ch.guild.voice_client.disconnect()
        AudioQueue.get(ch.guild.id).unregister()


bot.run(BOT_TOKEN)
