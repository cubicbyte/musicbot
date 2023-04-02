from pathlib import Path
from bot.schemas import Language
from . import unescape_string

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
            line = line[:-1] # Убрать символ переноса строки
            line = unescape_string(line) # Преобразовать экранированные символы в нормальные (e.g. \\n -> \n)

            if line == '' or line.startswith('#'):
                continue
            try:
                key, value = line.split('=', 1)
            except ValueError:
                raise ValueError(f'invalid line {i + 1} in {path}:\n"{line}"')

            lang[key] = value

    return lang
