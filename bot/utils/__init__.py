"""
Модуль с различными вспомогательными функциями
"""

import sponsorblock as sb
from ast import literal_eval
from pathlib import Path
from urllib.parse import urlparse
from ..schemas import Language



def load_lang_file(path: str) -> Language:
    """
    Загрузить файл .lang

    ### Пример использования::

        >>> lang = load_lang_file('langs/ru.lang')
        >>> print(lang['hello_world'])
        ... # Привет, мир!
        >>> print(lang['unexisting_key'])
        ... # unexisting_key (потому что ключа нет в словаре)

    ### Формат файла::

        # Комментарий
        # Комментарий с символом # внутри

        # Пустая строка выше ^
        hello_world=Привет, мир!
        error.something_went_wrong=Что-то пошло не так
        любой ключ перед знаком равно=любое значение с любыми символами

    :param path: Путь к файлу
    """

    lang = Language(lang_code=Path(path).stem)

    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line[:-1]                # Убрать символ переноса строки
            line = unescape_string(line)    # Преобразовать экранированные символы в нормальные (e.g. \\n -> \n)

            if line == '' or line.startswith('#'):
                continue

            try:
                key, value = line.split('=', 1)
            except ValueError:
                raise SyntaxError(f'invalid line {i + 1} in {path}:\n"{line}"')

            lang[key] = value

    return lang



def unescape_string(escaped_string: str) -> str:
    "Преобразовать строку с экранированными символами (e.g. \\n) в нормальную строку"

    return literal_eval(f'"{escaped_string}"')



def is_url(string: str) -> bool:
    "Проверить, является ли строка ссылкой"

    try:
        r = urlparse(string)
    except ValueError:
        return False

    return all([r.scheme, r.netloc])
