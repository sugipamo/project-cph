"""Mock output manager for testing."""
import contextlib
from typing import List, Optional, Union
from src.infrastructure.di_container import DIContainer
from src.utils.format_info import FormatInfo
from src.operations.results.__init__ import OutputManagerInterface
from src.utils.types import LogEntry, LogLevel

class MockOutputManager(OutputManagerInterface):
    """Mock implementation of OutputManagerInterface for testing."""

    def __init__(self, name: Optional[str], level: LogLevel):
        self.name = name
        self.level = level
        self.entries: List[LogEntry] = []
        self.captured_outputs: List[str] = []
        self.flush_calls: int = 0
        self._config_manager = None
        with contextlib.suppress(Exception):
            self._config_manager = DIContainer.resolve('config_manager')

    def add(self, message: Union[str, OutputManagerInterface], level: LogLevel, formatinfo: Optional[FormatInfo], realtime: bool) -> None:
        """Add entry to mock (no side effects)."""
        entry = LogEntry(message, level, formatinfo=formatinfo)
        self.entries.append(entry)
        if realtime:
            if isinstance(message, OutputManagerInterface):
                output_text = message.output()
            else:
                try:
                    if self._config_manager:
                        self._config_manager.resolve_config(['logging_config', 'mock_output', 'default_output_text'], str)
                        message_str = str(message)
                        if not message_str:
                            raise ValueError('Message cannot be empty when no default output is specified')
                        output_text = message_str
                    else:
                        raise KeyError('Config manager not available')
                except (KeyError, Exception) as e:
                    raise ValueError('Mock output default text configuration not found') from e
            self.captured_outputs.append(output_text)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if level should be logged."""
        return level.value >= self.level.value

    def _collect_entries(self, flatten: bool, sort: bool, level: LogLevel) -> List[LogEntry]:
        """Collect entries matching criteria."""

        def collect(entries):
            result = []
            for entry in entries:
                if entry.level.value >= level.value:
                    if flatten and isinstance(entry.content, OutputManagerInterface):
                        result.append(entry)
                    else:
                        result.append(entry)
            return result
        result = collect(self.entries)
        if sort:
            result.sort(key=lambda e: e.timestamp)
        return result

    def output(self, indent: int, level: LogLevel) -> str:
        """Generate mock output."""
        lines = []
        if self.name:
            lines.append('    ' * indent + self.name)
        for entry in self._collect_entries(False, False, level):
            lines.append(entry.formatted_content)
        return '\n'.join(lines)

    def flush(self) -> None:
        """Mock flush (no side effects)."""
        self.flush_calls += 1
        output = self.output(0, LogLevel.DEBUG)
        self.captured_outputs.append(output)

    def flatten(self, level: LogLevel) -> List[LogEntry]:
        """Get flattened entries."""
        return self._collect_entries(True, False, level)

    def output_sorted(self, level: LogLevel) -> str:
        """Generate sorted output."""
        entries = self._collect_entries(True, True, level)
        return '\n'.join((e.formatted_content for e in entries))

    def get_captured_outputs(self) -> List[str]:
        """Get captured outputs for testing."""
        return self.captured_outputs.copy()

    def get_flush_count(self) -> int:
        """Get number of flush calls."""
        return self.flush_calls

    def clear_captured(self) -> None:
        """Clear captured outputs."""
        self.captured_outputs.clear()
        self.flush_calls = 0