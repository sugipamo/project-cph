from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Union

from src.utils.format_info import FormatInfo
from src.utils.log_types import LogLevel as BaseLogLevel

if TYPE_CHECKING:
    from src.operations.interfaces.utility_interfaces import OutputManagerInterface

# Re-export LogLevel for backward compatibility
LogLevel = BaseLogLevel

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
