from typing import List, Optional, Union

from .format_info import FormatInfo
from .interfaces.output_manager_interface import OutputManagerInterface
from .types import LogEntry, LogLevel


class OutputManager(OutputManagerInterface):
    def __init__(
        self,
        name: Optional[str] = None,
        level: LogLevel = LogLevel.INFO
    ):
        self.name = name
        self.level = level
        self.entries: List[LogEntry] = []

    def add(self, message: Union[str, 'OutputManager'], level: LogLevel = LogLevel.INFO, formatinfo: Optional[FormatInfo] = None, realtime: bool = False):
        entry = LogEntry(message, level, formatinfo=formatinfo)
        self.entries.append(entry)
        if realtime:
            if isinstance(message, OutputManager):
                print(message.output())
            else:
                print(message)

    def _should_log(self, level: LogLevel):
        return level.value >= self.level.value

    def _collect_entries(self, flatten: bool = False, sort: bool = False, level: LogLevel = LogLevel.DEBUG):
        def collect(entries):
            result = []
            for entry in entries:
                if entry.level.value >= level.value:
                    if flatten and isinstance(entry.content, OutputManager):
                        result.extend(collect(entry.content.entries))
                    else:
                        result.append(entry)
            return result
        result = collect(self.entries)
        if sort:
            result.sort(key=lambda e: e.timestamp)
        return result

    def output(self, indent=0, level: LogLevel = LogLevel.DEBUG) -> str:
        lines = []
        if self.name:
            lines.append(('    ' * indent) + self.name)
        for entry in self._collect_entries(flatten=False, sort=False, level=level):
            lines.append(entry.formatted_content)
        return "\n".join(lines)

    def flush(self):
        print(self.output())

    def flatten(self, level: LogLevel = LogLevel.DEBUG) -> list:
        return self._collect_entries(flatten=True, sort=False, level=level)

    def output_sorted(self, level: LogLevel = LogLevel.DEBUG) -> str:
        entries = self._collect_entries(flatten=True, sort=True, level=level)
        return "\n".join(e.formatted_content for e in entries)

