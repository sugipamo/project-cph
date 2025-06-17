"""Logging module with dependency injection support."""

from .interfaces.output_manager_interface import OutputManagerInterface
from .mock_output_manager import MockOutputManager
from .output_manager import OutputManager
from .types import LogEntry, LogLevel, LogFormatType
from .format_info import FormatInfo

__all__ = [
    'OutputManagerInterface',
    'OutputManager',
    'MockOutputManager',
    'LogEntry',
    'LogLevel',
    'LogFormatType',
    'FormatInfo',
]
