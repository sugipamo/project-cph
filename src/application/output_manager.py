from typing import List, Optional, Union

from src.operations.interfaces.utility_interfaces import OutputManagerInterface
from src.utils.format_info import FormatInfo
from src.logging.types import LogEntry, LogLevel


class OutputManager(OutputManagerInterface):

    def __init__(self, name: Optional[str], level: LogLevel, output_driver=None):
        self.name = name
        self.level = level
        self.entries: List[LogEntry] = []
        self._output_driver = output_driver  # Injected output driver to avoid direct print()

    def add(self, message: Union[str, 'OutputManager'], level: LogLevel, formatinfo: Optional[FormatInfo], realtime: bool):
        entry = LogEntry(message, level, formatinfo=formatinfo)
        self.entries.append(entry)
        if realtime:
            if self._output_driver:
                if hasattr(message, 'output') and not isinstance(message, str):
                    self._output_driver.write(message.output(indent=0, level=LogLevel.DEBUG))
                else:
                    self._output_driver.write(str(message))
            # If no output driver injected, suppress output (no side effects)

    def _should_log(self, level: LogLevel):
        # Define level order for comparison
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        return level_order.get(level, 0) >= level_order.get(self.level, 0)

    def _collect_entries(self, flatten: bool, sort: bool, level: LogLevel):
        # Define level order for comparison
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }

        def collect(entries):
            result = []
            for entry in entries:
                if level_order.get(entry.level, 0) >= level_order.get(level, 0):
                    if flatten and hasattr(entry.content, 'entries'):
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
            lines.append('    ' * indent + self.name)
        for entry in self._collect_entries(False, False, level):
            lines.append(entry.formatted_content)
        return '\n'.join(lines)

    def flush(self):
        if self._output_driver:
            self._output_driver.write(self.output(0, LogLevel.DEBUG))
        # If no output driver injected, suppress output (no side effects)

    def flatten(self, level: LogLevel) -> list:
        return self._collect_entries(True, False, level)

    def output_sorted(self, level: LogLevel) -> str:
        entries = self._collect_entries(True, True, level)
        return '\n'.join(e.formatted_content for e in entries)

    def set_level(self, level: LogLevel) -> None:
        """ログレベルを動的に変更する"""
        self.level = level

    def get_level(self) -> LogLevel:
        """現在のログレベルを取得する"""
        return self.level
