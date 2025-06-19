"""Infrastructure providers - 副作用を集約するプロバイダー群"""

from .file_provider import FileProvider, MockFileProvider, SystemFileProvider
from .json_provider import JsonProvider, MockJsonProvider, SystemJsonProvider
from .os_provider import MockOsProvider, OsProvider, SystemOsProvider
from .registry_provider import MockRegistryProvider, RegistryProvider, SystemRegistryProvider
from .sqlite_provider import MockSQLiteProvider, SQLiteProvider, SystemSQLiteProvider
from .time_provider import FixedTimeProvider, MockTimeProvider, SystemTimeProvider, TimeProvider

__all__ = [
    # File providers
    'FileProvider',
    'FixedTimeProvider',
    # JSON providers
    'JsonProvider',
    'MockFileProvider',
    'MockJsonProvider',
    'MockOsProvider',
    'MockRegistryProvider',
    'MockSQLiteProvider',
    'MockTimeProvider',
    # OS providers
    'OsProvider',
    # Registry providers
    'RegistryProvider',
    # SQLite providers
    'SQLiteProvider',
    'SystemFileProvider',
    'SystemJsonProvider',
    'SystemOsProvider',
    'SystemRegistryProvider',
    'SystemSQLiteProvider',
    'SystemTimeProvider',
    # Time providers
    'TimeProvider'
]
