from enum import IntEnum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass(frozen=True)
class BaseLogEntry:
    content: str
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = None
    data: Optional[Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())