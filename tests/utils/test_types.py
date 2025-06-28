"""Tests for types module."""
from datetime import datetime
import pytest
from unittest.mock import Mock

from src.utils.types import LogLevel, LogEntry
from src.utils.format_info import FormatInfo


class TestLogEntry:
    """Test cases for LogEntry dataclass."""

    def test_init_with_string_content(self):
        """Test LogEntry initialization with string content."""
        entry = LogEntry(content="Test message")
        
        assert entry.content == "Test message"
        assert entry.level == LogLevel.INFO
        assert isinstance(entry.timestamp, datetime)
        assert entry.formatinfo is None

    def test_init_with_all_fields(self):
        """Test LogEntry initialization with all fields."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        formatinfo = Mock(spec=FormatInfo)
        
        entry = LogEntry(
            content="Error occurred",
            level=LogLevel.ERROR,
            timestamp=timestamp,
            formatinfo=formatinfo
        )
        
        assert entry.content == "Error occurred"
        assert entry.level == LogLevel.ERROR
        assert entry.timestamp == timestamp
        assert entry.formatinfo is formatinfo

    def test_formatted_content_with_string(self):
        """Test formatted_content property with string content."""
        entry = LogEntry(content="Plain text")
        assert entry.formatted_content == "Plain text"

    def test_formatted_content_with_format_info(self):
        """Test formatted_content property with FormatInfo."""
        formatinfo = Mock(spec=FormatInfo)
        formatinfo.apply.return_value = "FORMATTED: Test"
        
        entry = LogEntry(content="Test", formatinfo=formatinfo)
        
        assert entry.formatted_content == "FORMATTED: Test"
        formatinfo.apply.assert_called_once_with("Test")

    def test_formatted_content_with_output_manager(self):
        """Test formatted_content property with OutputManagerInterface content."""
        # Mock an OutputManagerInterface
        output_manager = Mock()
        output_manager.output.return_value = "Manager output"
        
        entry = LogEntry(content=output_manager)
        
        assert entry.formatted_content == "Manager output"
        output_manager.output.assert_called_once()

    def test_formatted_content_with_output_manager_and_format_info(self):
        """Test formatted_content with OutputManager content and FormatInfo."""
        # Mock OutputManagerInterface
        output_manager = Mock()
        output_manager.output.return_value = "Manager output"
        
        # Mock FormatInfo
        formatinfo = Mock(spec=FormatInfo)
        formatinfo.apply.return_value = "FORMATTED: Manager output"
        
        entry = LogEntry(content=output_manager, formatinfo=formatinfo)
        
        assert entry.formatted_content == "FORMATTED: Manager output"
        output_manager.output.assert_called_once()
        formatinfo.apply.assert_called_once_with("Manager output")

    def test_frozen_dataclass(self):
        """Test that LogEntry is frozen (immutable)."""
        entry = LogEntry(content="Test")
        
        with pytest.raises(AttributeError):
            entry.content = "Modified"
        
        with pytest.raises(AttributeError):
            entry.level = LogLevel.ERROR

    def test_timestamp_default_factory(self):
        """Test that timestamp uses current time by default."""
        before = datetime.now()
        entry = LogEntry(content="Test")
        after = datetime.now()
        
        assert before <= entry.timestamp <= after

    def test_log_level_backward_compatibility(self):
        """Test that LogLevel is properly re-exported."""
        from src.utils.types import LogLevel as TypesLogLevel
        from src.utils.log_types import LogLevel as BaseLogLevel
        
        # They should be the same enum
        assert TypesLogLevel is BaseLogLevel
        assert TypesLogLevel.INFO == BaseLogLevel.INFO

    def test_different_log_levels(self):
        """Test creating entries with different log levels."""
        debug_entry = LogEntry(content="Debug", level=LogLevel.DEBUG)
        info_entry = LogEntry(content="Info", level=LogLevel.INFO)
        warning_entry = LogEntry(content="Warning", level=LogLevel.WARNING)
        error_entry = LogEntry(content="Error", level=LogLevel.ERROR)
        critical_entry = LogEntry(content="Critical", level=LogLevel.CRITICAL)
        
        assert debug_entry.level == LogLevel.DEBUG
        assert info_entry.level == LogLevel.INFO
        assert warning_entry.level == LogLevel.WARNING
        assert error_entry.level == LogLevel.ERROR
        assert critical_entry.level == LogLevel.CRITICAL

    def test_equality(self):
        """Test LogEntry equality."""
        timestamp = datetime.now()
        formatinfo = Mock(spec=FormatInfo)
        
        entry1 = LogEntry(
            content="Test",
            level=LogLevel.INFO,
            timestamp=timestamp,
            formatinfo=formatinfo
        )
        entry2 = LogEntry(
            content="Test",
            level=LogLevel.INFO,
            timestamp=timestamp,
            formatinfo=formatinfo
        )
        entry3 = LogEntry(
            content="Different",
            level=LogLevel.INFO,
            timestamp=timestamp,
            formatinfo=formatinfo
        )
        
        assert entry1 == entry2
        assert entry1 != entry3

    def test_hash(self):
        """Test that LogEntry is hashable."""
        timestamp = datetime.now()
        entry = LogEntry(
            content="Test",
            level=LogLevel.INFO,
            timestamp=timestamp
        )
        
        # Should be able to use as dict key or in set
        entry_set = {entry}
        assert entry in entry_set
        
        entry_dict = {entry: "value"}
        assert entry_dict[entry] == "value"