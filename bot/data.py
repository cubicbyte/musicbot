"""
Module for working with data
"""

import os
import pathlib
import time
import json
import sqlite3

from settings import LANGS_DIR
from bot.audio import AudioQueue
from bot.schemas import SpamState, Language, YoutubeVideo
from bot.utils import load_lang_file

LANG_FILE_EXT_WHITELIST = ['.yaml', '.yml']
"Whitelist of localization file extensions that will be loaded"


def _load_langs(path: str) -> dict[str, Language]:
    """Load languages from specified directory"""

    _langs = {}

    for file in os.listdir(path):
        file_ext = pathlib.Path(file).suffix

        if file_ext not in LANG_FILE_EXT_WHITELIST:
            continue

        lang = load_lang_file(f'{path}/{file}')
        _langs[lang.lang_code] = lang

    return _langs


class BotDatabase:
    """
    Bot database.

    Stores bot language, saved youtube videos and other data
    """

    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Initialize database"""

        self._db.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY,
                lang_code TEXT,
                saves JSON
            );
        ''')
        self._db.commit()

    @staticmethod
    def _saves_deserializer(_dict: dict) -> dict[str, YoutubeVideo]:
        """
        Deserializer for saved songs

        Basically, it parses songs from database saved in json format
        and converts them to readable format for program
        """

        if 'title' in _dict:
            return YoutubeVideo(**_dict)

        return _dict

    def _get_field(self, guild_id: int, field: str) -> str | None:
        """Get field value from database by key"""

        row = self._db.execute(
            f'SELECT {field} FROM guilds WHERE guild_id = ?',
            (guild_id,)).fetchone()

        if row is None:
            return None

        return row[field]

    def _set_field(self, guild_id: int, field: str, value: any) -> None:
        """Set field value in database by key"""

        self._db.execute(
            f'INSERT OR REPLACE INTO guilds (guild_id, {field}) VALUES (?, ?)',
            (guild_id, value))

        self._db.commit()

    def get_guild_lang(self, guild_id: int) -> str | None:
        """Get guild language"""
        return self._get_field(guild_id, 'lang_code')

    def set_guild_lang(self, guild_id: int, lang_code: str) -> None:
        """Set guild language"""
        self._set_field(guild_id, 'lang_code', lang_code)

    def get_guild_yt_saves(self, guild_id: int) -> dict[str, YoutubeVideo]:
        """Get saved songs list"""

        res = self._get_field(guild_id, 'saves')
        if res is None:
            return {}

        saves = json.loads(res, object_hook=self._saves_deserializer)
        return saves

    def set_guild_yt_saves(self, guild_id: int, saves: dict[str, YoutubeVideo]) -> None:
        """Set saved songs list"""
        json_str = json.dumps(saves, default=lambda o: o.__dict__)
        self._set_field(guild_id, 'saves', json_str)


class GuildData:
    """Data for server"""

    MOVE_CD_S = 0.75
    "Cooldown for bot move between voice channels (in seconds)"

    database: BotDatabase
    "Bot database"
    _global_data = {}
    "Global data mapping for all servers"

    def __init__(self, guild_id: int) -> None:
        self.guild_id = guild_id
        "Server ID"
        self.spam: SpamState | None = None
        "Current spam state"
        self._last_move_timestamp: float = 0
        "Timestamp of last bot move"
        self._lang_code: str = self.database.get_guild_lang(guild_id) or os.getenv('DEFAULT_LANG')
        "Server language code"

    @property
    def queue(self) -> AudioQueue:
        """Audio queue for server"""
        return AudioQueue.get_queue(self.guild_id)

    @staticmethod
    def get_instance(guild_id: int) -> 'GuildData':
        """Get GuildData instance for server with specified ID"""

        _guild_id = str(guild_id)
        guild_data = GuildData._global_data.get(_guild_id)

        # Register new instance if needed
        if guild_data is None:
            guild_data = GuildData(guild_id)
            GuildData._global_data[_guild_id] = guild_data

        return guild_data

    def create_spam(self, message: str, repeats: int, delay: float) -> SpamState:
        """Create new `SpamState` instance"""
        self.spam = SpamState(message, repeats, delay)
        return self.spam

    def make_move(self) -> bool:
        """Register bot move to voice channel and return True if cooldown passed"""

        cur_timestamp = time.time()
        if cur_timestamp - self._last_move_timestamp < GuildData.MOVE_CD_S:
            return False

        self._last_move_timestamp = cur_timestamp
        return True

    def save_yt_video(self, video: YoutubeVideo, name: str) -> dict[str, YoutubeVideo]:
        """Save video to database"""

        saves = self.database.get_guild_yt_saves(self.guild_id)
        saves[name] = video

        self.database.set_guild_yt_saves(self.guild_id, saves)
        return saves

    def get_yt_saves(self) -> dict[str, YoutubeVideo]:
        """Get saved videos list"""
        return self.database.get_guild_yt_saves(self.guild_id)

    def get_saved_yt_video(self, name: str) -> YoutubeVideo | None:
        """Get saved video by name"""
        return self.database.get_guild_yt_saves(self.guild_id).get(name)

    def delete_saved_yt_video(self, name: str) -> dict[str, YoutubeVideo]:
        """Delete saved video by name"""

        saves = self.database.get_guild_yt_saves(self.guild_id)
        del saves[name]

        self.database.set_guild_yt_saves(self.guild_id, saves)
        return saves

    def clear_yt_saves(self) -> None:
        """Clear saved videos list"""
        self.database.set_guild_yt_saves(self.guild_id, {})

    def delete(self):
        """Delete GuildData instance"""
        self.queue.delete()

    @property
    def lang_code(self) -> str:
        """Server language code"""
        return self._lang_code

    @lang_code.setter
    def lang_code(self, value: str) -> None:
        self._lang_code = value
        self.database.set_guild_lang(self.guild_id, value)

    @property
    def lang(self) -> Language:
        """Server language"""
        return langs[self._lang_code]


database: 'BotDatabase' = BotDatabase('bot-data.sqlite')
"Bot database"
langs: dict[str, Language] = _load_langs(LANGS_DIR)
"Loaded languages"

GuildData.database = database


# Check default language validity
assert os.getenv('DEFAULT_LANG') in langs, (
    f'Field DEFAULT_LANG in .env file has invalid language: {os.getenv("DEFAULT_LANG")}. Available languages: ({", ".join(langs.keys())})')
