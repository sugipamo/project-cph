from typing import List, Optional, Union

from .format_info import FormatInfo
from .interfaces.output_manager_interface import OutputManagerInterface
from .types import LogEntry, LogLevel


class OutputManager(OutputManagerInterface):
    def __init__(
        self,
        name: Optional[str],
        level: LogLevel
    ):
        self.name = name
        self.level = level
        self.entries: List[LogEntry] = []

    def add(self, message: Union[str, 'OutputManager'], level: LogLevel, formatinfo: Optional[FormatInfo], realtime: bool):
        entry = LogEntry(message, level, formatinfo=formatinfo)
        self.entries.append(entry)
        if realtime:
            if isinstance(message, OutputManager):
                print(message.output())
            else:
                print(message)

    def _should_log(self, level: LogLevel):
        return level.value >= self.level.value

    def _collect_entries(self, flatten: bool, sort: bool, level: LogLevel):
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

    def output(self, indent: int, level: LogLevel) -> str:
        lines = []
        if self.name:
            lines.append(('    ' * indent) + self.name)
        for entry in self._collect_entries(False, False, level):
            lines.append(entry.formatted_content)
        return "\n".join(lines)

    def flush(self):
        print(self.output(0, LogLevel.DEBUG))

    def flatten(self, level: LogLevel) -> list:
        return self._collect_entries(True, False, level)

    def output_sorted(self, level: LogLevel) -> str:
        entries = self._collect_entries(True, True, level)
        return "\n".join(e.formatted_content for e in entries)

