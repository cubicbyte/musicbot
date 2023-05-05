"""
Модуль с различными вспомогательными функциями
"""

from ast import literal_eval
from pathlib import Path
from urllib.parse import urlparse

import flatdict
import yaml

from bot.schemas import Language


def load_lang_file(path: str) -> Language:
    """
    Загрузить лакализационный файл в формате YAML

    ### Пример использования::

        >>> lang = load_lang_file('langs/ru.yaml')
        >>> print(lang['hello_world'])
        ... # Привет, мир!
        >>> print(lang['unexisting_key'])
        ... # unexisting_key (потому что ключа нет в словаре)

    :param path: Путь к файлу
    """

    lang_code = Path(path).stem

    with open(path, encoding='utf-8') as f:
        try:
            data = yaml.load(f, Loader=yaml.FullLoader)
            data_flat = flatdict.FlatDict(data, delimiter='.')
        except (yaml.YAMLError, TypeError) as e:
            raise SyntaxError('Неверный формат файла локализации: %s' % lang_code) from e

    lang = Language(lang=data_flat, code=lang_code)

    return lang


def unescape_string(escaped_string: str) -> str:
    """Преобразовать строку с экранированными символами (e.g. \\n) в нормальную строку"""

    return literal_eval(f'"{escaped_string}"')


def is_url(string: str) -> bool:
    """Проверить, является ли строка ссылкой"""

    try:
        res = urlparse(string)
    except ValueError:
        return False

    return all([res.scheme, res.netloc])
