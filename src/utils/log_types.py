from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class BaseLogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    data: Optional[Any] = None