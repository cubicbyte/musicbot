"""
Module with all settings and global variables
"""

import os
import sys
import logging
import shutil

from dotenv import load_dotenv
from discord.ext import commands
from discord.flags import Intents

# Load environment variables (bot config)
load_dotenv()        # From .env file in project root
load_dotenv('.env')  # From .env file in current directory

os.environ.setdefault('BOT_COMMAND_PREFIX', '$')
os.environ.setdefault('DEFAULT_LANG', 'ru')
os.environ.setdefault('SAVES_LIMIT', '16')
os.environ.setdefault('LOG_FILEPATH', 'debug.log')
os.environ.setdefault('LOG_LEVEL', 'INFO')
os.environ.setdefault('ENABLE_SPONSORBLOCK', 'true')
os.environ.setdefault('LOG_FORMAT', logging.BASIC_FORMAT)

# Setup logging
os.makedirs(os.path.dirname(os.path.join('.', os.getenv('LOG_FILEPATH'))), exist_ok=True)
logging.basicConfig(
    level=os.getenv('LOG_LEVEL'),
    filename=os.getenv('LOG_FILEPATH'),
    filemode='a',
    format=os.getenv('LOG_FORMAT')
)
_logger = logging.getLogger(__name__)
_logger.info('Loading settings...')

LANGS_DIR = os.path.join(sys.path[0], 'langs')

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-bufsize 16M',
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'default_search': 'auto',
    'simulate': True,
}

if shutil.which('ffmpeg') is not None:
    FFMPEG_OPTIONS['executable'] = 'ffmpeg'
elif shutil.which('static_ffmpeg') is not None:
    FFMPEG_OPTIONS['executable'] = 'static_ffmpeg'
else:
    raise EnvironmentError(
        'FFmpeg not found. Please install FFmpeg and make sure it is in your system PATH.'
        'Alternatively, you can use static-ffmpeg package to include FFmpeg binary with the bot.'
    )

if os.path.exists('cookies.txt'):  # For YouTube age-restricted videos and videos with other restrictions
    YDL_OPTIONS['cookies'] = 'cookies.txt'
    _logger.info('Using cookies.txt for YouTube video downloads')
else:
    _logger.warning('No cookies.txt found, some YouTube videos may not be playable')

# Check environment variables
_ENV_HELP = 'Please read README.md to learn how to configure bot.'
assert os.getenv('BOT_TOKEN') is not None, 'BOT_TOKEN not specified. ' + _ENV_HELP
assert os.getenv('SAVES_LIMIT').isdigit(), 'SAVES_LIMIT should be integer. ' + _ENV_HELP

indents = Intents.default()
indents.message_content = True
bot = commands.Bot(command_prefix=os.getenv('BOT_COMMAND_PREFIX'), intents=indents)
