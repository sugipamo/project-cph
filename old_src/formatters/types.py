from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from .format_info import FormatInfo
    from .output_manager import OutputManager

class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

class LogFormatType(Enum):
    RAW = auto()
    PLAIN = auto()
    CUSTOM = auto()

@dataclass(frozen=True)
class LogEntry:
    content: Union[str, 'OutputManager']
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    formatinfo: Optional['FormatInfo'] = None

    @property
    def formatted_content(self) -> str:
        text = self.content if isinstance(self.content, str) else self.content.output()
        if self.formatinfo:
            # 循環インポート回避のため、ここでメソッド呼び出し
            return self.formatinfo.apply(text)
        return text
