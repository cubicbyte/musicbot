import os
import logging
from discord.ext import commands
from discord.flags import Intents
from config import BOT_COMMAND_PREFIX, LOG_LEVEL, LOG_FILEPATH, LOG_FORMAT



os.makedirs(os.path.dirname(LOG_FILEPATH), exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    filename=LOG_FILEPATH,
    filemode='a',
    format=LOG_FORMAT
)

_logger = logging.getLogger(__name__)
_logger.info('Loading settings...')



indents = Intents.default()
indents.message_content = True
bot = commands.Bot(command_prefix=BOT_COMMAND_PREFIX, intents=indents)
