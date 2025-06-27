from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Union

from src.utils.format_info import FormatInfo

if TYPE_CHECKING:
    from src.operations.interfaces.output_manager_interface import OutputManagerInterface

class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

@dataclass(frozen=True)
class LogEntry:
    content: Union[str, 'OutputManagerInterface']
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    formatinfo: Optional[FormatInfo] = None

    @property
    def formatted_content(self) -> str:
        text = self.content if isinstance(self.content, str) else self.content.output()
        if self.formatinfo:
            return self.formatinfo.apply(text)
        return text
