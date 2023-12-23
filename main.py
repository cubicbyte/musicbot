import os
import logging
import bot.commands as _

from settings import bot
from bot.data import GuildData, AudioQueue
from bot.utils.discord_utils import is_users_in_channel, get_bot_channel

logger = logging.getLogger('bot')


@bot.event
async def on_ready():
    """Runs when bot is ready"""
    logger.info('Bot is ready!')


@bot.event
async def on_voice_state_update(member, before, after):
    """
    Leave channel if it's empty, or move to user channel
    if he changed channel and bot is alone.
    """

    if member.bot:
        return

    ch = get_bot_channel(bot, before, after)

    # Ignore if it's not bot channel
    if ch is None:
        return

    # Ignore if bot channel has users
    if is_users_in_channel(ch):
        return

    # Go to user channel if he changed channel
    if after is not None and after.channel is not None:
        if after.channel.id == ch.id:
            return
        if GuildData.get_instance(ch.guild.id).make_move():
            await ch.guild.voice_client.move_to(after.channel)

    # Leave channel
    else:
        # Protection from accidental channel disconnect
        # Bot will disconnect if user will not return to channel in 750ms
        # await sleep(0.75)
        # if not is_users_in_channel(ch):
        await ch.guild.voice_client.disconnect()
        AudioQueue.del_queue(ch.guild.id)


bot.run(os.getenv('BOT_TOKEN'))
