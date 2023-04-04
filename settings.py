import os
import logging
from discord.ext import commands
from discord.flags import Intents

# Проверка наличия файла config.py
try:
    import config
except ImportError:
    raise ImportError('Файл config.py не найден. Пожалуйста, прочтите файл README.md, пункт 1.')

# Проверка наличия всех обязательных параметров
assert config.BOT_TOKEN != '', 'BOT_TOKEN не указан. Пожалуйста, укажите его в файле config.py'



# Создание папки логов
os.makedirs(os.path.dirname(os.path.join('.', config.LOG_FILEPATH)), exist_ok=True)

logging.basicConfig(
    level=config.LOG_LEVEL,
    filename=config.LOG_FILEPATH,
    filemode='a',
    format=config.LOG_FORMAT
)

_logger = logging.getLogger(__name__)
_logger.info('Loading settings...')



indents = Intents.default()
indents.message_content = True
bot = commands.Bot(command_prefix=config.BOT_COMMAND_PREFIX, intents=indents)
