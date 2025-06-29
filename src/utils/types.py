from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Union

from src.utils.format_info import FormatInfo
from src.logging.log_types import LogLevel as BaseLogLevel

# Re-export LogLevel for backward compatibility
LogLevel = BaseLogLevel

@dataclass(frozen=True)
class LogEntry:
    content: Union[str, Any]  # Any object with output() method
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    formatinfo: Optional[FormatInfo] = None

    @property
    def formatted_content(self) -> str:
        if isinstance(self.content, str):
            text = self.content
        else:
            # Duck typing: assume content has output() method
            text = self.content.output()
        
        if self.formatinfo:
            return self.formatinfo.apply(text)
        return text
