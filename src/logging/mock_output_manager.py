"""Mock output manager for testing."""

from typing import List, Optional, Union

from .format_info import FormatInfo
from .interfaces.output_manager_interface import OutputManagerInterface
from .types import LogEntry, LogLevel


class MockOutputManager(OutputManagerInterface):
    """Mock implementation of OutputManagerInterface for testing."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        level: LogLevel = LogLevel.INFO
    ):
        self.name = name
        self.level = level
        self.entries: List[LogEntry] = []
        self.captured_outputs: List[str] = []
        self.flush_calls: int = 0

    def add(
        self,
        message: Union[str, OutputManagerInterface],
        level: LogLevel = LogLevel.INFO,
        formatinfo: Optional[FormatInfo] = None,
        realtime: bool = False
    ) -> None:
        """Add entry to mock (no side effects)."""
        entry = LogEntry(message, level, formatinfo=formatinfo)
        self.entries.append(entry)
        
        if realtime:
            output_text = message.output() if isinstance(message, OutputManagerInterface) else str(message)
            self.captured_outputs.append(output_text)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if level should be logged."""
        return level.value >= self.level.value

    def _collect_entries(self, flatten: bool = False, sort: bool = False, level: LogLevel = LogLevel.DEBUG) -> List[LogEntry]:
        """Collect entries matching criteria."""
        def collect(entries):
            result = []
            for entry in entries:
                if entry.level.value >= level.value:
                    if flatten and isinstance(entry.content, OutputManagerInterface):
                        # For mock, we don't have nested entries, so just add the entry
                        result.append(entry)
                    else:
                        result.append(entry)
            return result
            
        result = collect(self.entries)
        if sort:
            result.sort(key=lambda e: e.timestamp)
        return result

    def output(self, indent: int = 0, level: LogLevel = LogLevel.DEBUG) -> str:
        """Generate mock output."""
        lines = []
        if self.name:
            lines.append(('    ' * indent) + self.name)
        for entry in self._collect_entries(flatten=False, sort=False, level=level):
            lines.append(entry.formatted_content)
        return "\n".join(lines)

    def flush(self) -> None:
        """Mock flush (no side effects)."""
        self.flush_calls += 1
        output = self.output()
        self.captured_outputs.append(output)

    def flatten(self, level: LogLevel = LogLevel.DEBUG) -> List[LogEntry]:
        """Get flattened entries."""
        return self._collect_entries(flatten=True, sort=False, level=level)

    def output_sorted(self, level: LogLevel = LogLevel.DEBUG) -> str:
        """Generate sorted output."""
        entries = self._collect_entries(flatten=True, sort=True, level=level)
        return "\n".join(e.formatted_content for e in entries)

    # Test utility methods
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