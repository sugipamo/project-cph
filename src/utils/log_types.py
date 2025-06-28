"""Log-related type definitions without circular dependencies."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass(frozen=True)
class BaseLogEntry:
    """Base log entry without output manager dependency."""
    content: str
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)