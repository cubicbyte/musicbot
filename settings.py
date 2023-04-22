"""
Модуль со всеми настройками и глобальными переменными
"""

import os
import sys
import logging
from dotenv import load_dotenv
from discord.ext import commands
from discord.flags import Intents



# Загрузка переменных окружения (конфиг бота)
load_dotenv()       # Из файла .env в папке бота
load_dotenv('.env') # Из файла .env в папке, откуда был запущен бот

LANGS_DIR = os.path.join(sys.path[0], 'langs')

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'executable': 'static_ffmpeg'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'default_search': 'auto',
    'simulate': True,
}

os.environ.setdefault('BOT_COMMAND_PREFIX', '$')
os.environ.setdefault('DEFAULT_LANG', 'ru')
os.environ.setdefault('LOG_FILEPATH', 'debug.log')
os.environ.setdefault('LOG_LEVEL', 'INFO')
os.environ.setdefault('LOG_FORMAT', logging.BASIC_FORMAT)

# Проверка параметров
_ENV_HELP = 'Пожалуйста, прочитайте README.md, чтобы узнать, как настроить бота.'
assert os.getenv('BOT_TOKEN') is not None, 'BOT_TOKEN не указан. ' + _ENV_HELP



# Создание папки логов
os.makedirs(os.path.dirname(os.path.join('.', os.getenv('LOG_FILEPATH'))), exist_ok=True)

logging.basicConfig(
    level=os.getenv('LOG_LEVEL'),
    filename=os.getenv('LOG_FILEPATH'),
    filemode='a',
    format=os.getenv('LOG_FORMAT')
)

_logger = logging.getLogger(__name__)
_logger.info('Loading settings...')



indents = Intents.default()
indents.message_content = True
bot = commands.Bot(command_prefix=os.getenv('BOT_COMMAND_PREFIX'), intents=indents)
