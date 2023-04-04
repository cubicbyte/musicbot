# Обязательные

BOT_TOKEN = ''


# Необязательные

BOT_COMMAND_PREFIX = '$'
DEFAULT_LANG = 'ru' # Все доступные языки находятся в папке, указанной в LANGS_DIR

LANGS_DIR = 'langs'
LOG_FILEPATH = 'debug.log'

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'executable': 'static_ffmpeg'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'default_search': 'auto',
    'simulate': True,
}
