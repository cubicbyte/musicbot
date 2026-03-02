"""
Module for working with data
"""

import os
import pathlib
import time
import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass

from settings import LANGS_DIR
from bot.audio import AudioQueue
from bot.schemas import SpamState, Language, YoutubeVideo, AudioSource
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


@dataclass
class SavedAudio:
    """Saved audio data"""

    name: str
    "Audio name"
    type: str
    "Audio source type (YouTube video, SoundCloud, etc.)"
    source: AudioSource
    "Audio source"


class BotDatabaseRepository(ABC):
    """
    Abstract class for bot database repository

    It's used for storing data in database
    """

    @abstractmethod
    def get_guild_saved_audio(self, guild_id: int) -> list[SavedAudio]:
        """Get saved audio list"""

    @abstractmethod
    def set_guild_saved_audio(self, guild_id: int, saves: list[SavedAudio]) -> None:
        """Set saved audio list"""

    @abstractmethod
    def get_guild_language(self, guild_id: int) -> str:
        """Get guild language"""

    @abstractmethod
    def set_guild_language(self, guild_id: int, lang_code: str) -> None:
        """Set guild language"""

    def save_guild_audio(self, guild_id: int, audio: SavedAudio) -> None:
        """Save audio to database"""
        saves = self.get_guild_saved_audio(guild_id)
        saves.append(audio)
        self.set_guild_saved_audio(guild_id, saves)

    def delete_guild_audio(self, guild_id: int, name: str) -> None:
        """Delete audio from database"""
        name = name.lower()
        saves = self.get_guild_saved_audio(guild_id)
        saves = filter(lambda audio: audio.name.lower() != name, saves)
        self.set_guild_saved_audio(guild_id, saves)

    def get_guild_saved_audio_by_name(self, guild_id: int, name: str) -> SavedAudio | None:
        """Get saved audio by name"""

        name = name.lower()
        for audio in self.get_guild_saved_audio(guild_id):
            if audio.name.lower() == name:
                return audio

        return None

    def clear_guild_saved_audio(self, guild_id: int) -> None:
        """Clear guild YouTube saves"""
        self.set_guild_saved_audio(guild_id, [])


class SQLiteBotDatabase(BotDatabaseRepository):
    """Bot database based on SQLite"""

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

    def _init_guild(self, guild_id: int):
        """Initialize guild in database if it doesn't exist"""

        row = self._db.execute(
            f'SELECT guild_id FROM guilds WHERE guild_id = ?',
            (guild_id,)).fetchone()

        if row is None:
            self._db.execute(
                f'INSERT INTO guilds (guild_id, lang_code, saves) VALUES (?, ?, ?)',
                (guild_id, os.getenv('DEFAULT_LANG'), json.dumps([])))
            self._db.commit()

    def get_guild_language(self, guild_id: int) -> str | None:
        row = self._db.execute(
            f'SELECT lang_code FROM guilds WHERE guild_id = ?',
            (guild_id,)).fetchone()

        if row is None:
            return None

        return row['lang_code']

    def set_guild_language(self, guild_id: int, lang_code: str) -> None:
        self._db.execute(
            f'INSERT OR REPLACE INTO guilds (guild_id, lang_code) VALUES (?, ?)',
            (guild_id, lang_code))

        self._db.commit()

    def get_guild_saved_audio(self, guild_id: int) -> list[SavedAudio]:
        """Get saved audio list"""

        row = self._db.execute(
            'SELECT saves FROM guilds WHERE guild_id = ?',
            (guild_id,)).fetchone()

        if row is None:
            return []

        saves = json.loads(row['saves'])
        audio_list = []
        for name, type_, data in saves:
            if type_ == 'youtube':
                source = YoutubeVideo.deserialize(data)
            else:
                source = AudioSource.deserialize(data)
            audio_list.append(SavedAudio(name, type_, source))
        return audio_list

    def set_guild_saved_audio(self, guild_id: int, saves: list[SavedAudio]) -> None:
        """Set saved audio list"""

        self._init_guild(guild_id)
        self._db.execute(
            'UPDATE guilds SET saves = ? WHERE guild_id = ?',
            (json.dumps([(audio.name, audio.type, audio.source.serialize()) for audio in saves]), guild_id))

        self._db.commit()


class GuildData:
    """Data for server"""

    MOVE_COOLDOWN = 0.75
    "Cooldown for bot move between voice channels (in seconds)"

    database: SQLiteBotDatabase
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
        self._lang_code: str = self.database.get_guild_language(guild_id) or os.getenv('DEFAULT_LANG')
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
        if cur_timestamp - self._last_move_timestamp < GuildData.MOVE_COOLDOWN:
            return False

        self._last_move_timestamp = cur_timestamp
        return True

    def save_audio(self, audio: AudioSource, name: str) -> None:
        """Save YouTube video to database"""
        if isinstance(audio, YoutubeVideo):
            audio_type = 'youtube'
        else:
            audio_type = 'unknown'
        self.database.save_guild_audio(self.guild_id, SavedAudio(name, audio_type, audio))

    def get_saved_audio(self) -> list[SavedAudio]:
        """Get saved audio list"""
        return self.database.get_guild_saved_audio(self.guild_id)

    def get_saved_audio_by_name(self, name: str) -> SavedAudio | None:
        """Get saved audio by name"""
        return self.database.get_guild_saved_audio_by_name(self.guild_id, name)

    def delete_saved_audio(self, name: str) -> None:
        """Delete saved audio by name"""
        self.database.delete_guild_audio(self.guild_id, name)

    def clear_saves(self) -> None:
        """Clear saved audio list"""
        self.database.clear_guild_saved_audio(self.guild_id)

    def delete(self):
        """Delete GuildData instance"""
        self.queue.delete()

    @property
    def lang_code(self) -> str:
        """Server language code"""
        # TODO: don't set this on __init__, get and cache it here instead
        return self._lang_code

    @lang_code.setter
    def lang_code(self, value: str) -> None:
        self._lang_code = value
        self.database.set_guild_language(self.guild_id, value)

    @property
    def lang(self) -> Language:
        """Server language"""
        return langs[self._lang_code]


database: 'SQLiteBotDatabase' = SQLiteBotDatabase('bot-data.sqlite')
"Bot database"
langs: dict[str, Language] = _load_langs(LANGS_DIR)
"Loaded languages"

GuildData.database = database


# Check default language validity
assert os.getenv('DEFAULT_LANG') in langs, (
    f'Field DEFAULT_LANG in .env file has invalid language: {os.getenv("DEFAULT_LANG")}. Available languages: ({", ".join(langs.keys())})')
