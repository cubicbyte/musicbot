"""
Utilities for work with Discord
"""

from discord import VoiceState, VoiceChannel, VoiceClient, User
from discord.ext.commands import Bot


def is_users_in_channel(channel: VoiceChannel):
    """Check if there is any users in voice channel. Bots are not counted."""

    for member in channel.members:
        if not member.bot:
            return True

    return False


def is_connected(bot: Bot, channel: VoiceChannel):
    """Check if bot is connected to voice channel"""

    for member in channel.members:
        if member.id == bot.user.id:
            return True

    return False


def get_bot_channel(bot: Bot, *states: VoiceState | None) -> VoiceChannel | None:
    """Get voice channel where bot is"""

    for state in states:
        if state is None or state.channel is None:
            continue

        if is_connected(bot, state.channel):
            return state.channel

    return None


def is_user_in_bot_channel(voice_client: VoiceClient, user: User) -> bool:
    """Check if user is in bot voice channel"""

    if voice_client is None or user.voice is None:
        return False

    return user.voice.channel.id == voice_client.channel.id
