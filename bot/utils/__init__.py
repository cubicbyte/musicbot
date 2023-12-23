"""
Module with various helper functions
"""

from ast import literal_eval
from pathlib import Path
from urllib.parse import urlparse

import flatdict
import yaml

from bot.schemas import Language


def load_lang_file(path: str) -> Language:
    """
    Load localization file in YAML format

    ### Usage example::

        >>> lang = load_lang_file('langs/en.yaml')
        >>> print(lang['hello_world'])
        ... # Hello, world!
        >>> print(lang['unexisting_key'])
        ... # unexisting_key (because key doesn't exist in dictionary)

    :param path: Path to file
    """

    lang_code = Path(path).stem

    with open(path, encoding='utf-8') as f:
        try:
            data = yaml.load(f, Loader=yaml.FullLoader)
            data_flat = flatdict.FlatDict(data, delimiter='.')
        except (yaml.YAMLError, TypeError) as e:
            raise SyntaxError('Invalid localization file format: %s' % lang_code) from e

    lang = Language(lang=data_flat, code=lang_code)

    return lang


def unescape_string(escaped_string: str) -> str:
    """Convert string with escaped characters (e.g. \\n) to normal string"""

    return literal_eval(f'"{escaped_string}"')


def is_url(string: str) -> bool:
    """Check if string is URL"""

    try:
        res = urlparse(string)
    except ValueError:
        return False

    return all([res.scheme, res.netloc])
