"""Tests for OutputManager class."""
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.output_manager import OutputManager
from src.infrastructure.drivers.logging.types import LogEntry, LogLevel


class TestOutputManager:
    """Test cases for OutputManager class."""

    def test_init_default_values(self):
        """Test OutputManager initialization with default values."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        assert manager.name is None
        assert manager.level == LogLevel.INFO
        assert manager.entries == []

    def test_init_with_custom_values(self):
        """Test OutputManager initialization with custom values."""
        manager = OutputManager(name="test_logger", level=LogLevel.DEBUG)
        assert manager.name == "test_logger"
        assert manager.level == LogLevel.DEBUG
        assert manager.entries == []

    def test_add_string_message(self):
        """Test adding a string message."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        assert len(manager.entries) == 1
        entry = manager.entries[0]
        assert entry.content == "Test message"
        assert entry.level == LogLevel.INFO
        assert entry.formatinfo is None

    def test_add_string_message_with_formatinfo(self):
        """Test adding a string message with format info."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        format_info = FormatInfo(color="red", bold=True)
        manager.add("Test message", LogLevel.ERROR, formatinfo=format_info, realtime=False)

        assert len(manager.entries) == 1
        entry = manager.entries[0]
        assert entry.content == "Test message"
        assert entry.level == LogLevel.ERROR
        assert entry.formatinfo == format_info

    def test_add_output_manager_message(self):
        """Test adding an OutputManager as a message."""
        parent_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager.add("Child message", LogLevel.INFO, formatinfo=None, realtime=False)

        parent_manager.add(child_manager, LogLevel.INFO, formatinfo=None, realtime=False)

        assert len(parent_manager.entries) == 1
        entry = parent_manager.entries[0]
        assert entry.content == child_manager
        assert entry.level == LogLevel.INFO

    @patch('builtins.print')
    def test_add_with_realtime_string(self, mock_print):
        """Test adding message with realtime=True for string."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=True)

        mock_print.assert_called_once_with("Test message")

    @patch('builtins.print')
    def test_add_with_realtime_output_manager(self, mock_print):
        """Test adding message with realtime=True for OutputManager."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager.add("Child message", LogLevel.INFO, formatinfo=None, realtime=False)

        manager.add(child_manager, LogLevel.INFO, formatinfo=None, realtime=True)

        mock_print.assert_called_once_with(child_manager.output(indent=0, level=LogLevel.DEBUG))

    def test_should_log_with_same_level(self):
        """Test _should_log with same log level."""
        manager = OutputManager(name=None, level=LogLevel.WARNING)
        assert manager._should_log(LogLevel.WARNING) is True

    def test_should_log_with_higher_level(self):
        """Test _should_log with higher log level."""
        manager = OutputManager(name=None, level=LogLevel.WARNING)
        assert manager._should_log(LogLevel.ERROR) is True

    def test_should_log_with_lower_level(self):
        """Test _should_log with lower log level."""
        manager = OutputManager(name=None, level=LogLevel.WARNING)
        assert manager._should_log(LogLevel.INFO) is False

    def test_collect_entries_simple(self):
        """Test _collect_entries with simple entries."""
        manager = OutputManager(name=None, level=LogLevel.DEBUG)
        manager.add("Debug message", LogLevel.DEBUG, formatinfo=None, realtime=False)
        manager.add("Info message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Error message", LogLevel.ERROR, formatinfo=None, realtime=False)

        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.INFO)
        assert len(entries) == 2
        assert entries[0].content == "Info message"
        assert entries[1].content == "Error message"

    def test_collect_entries_with_nested_managers(self):
        """Test _collect_entries with nested OutputManagers."""
        parent_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager.add("Child message", LogLevel.INFO, formatinfo=None, realtime=False)

        parent_manager.add("Parent message", LogLevel.INFO, formatinfo=None, realtime=False)
        parent_manager.add(child_manager, LogLevel.INFO, formatinfo=None, realtime=False)

        # Test without flattening
        entries = parent_manager._collect_entries(flatten=False, sort=False, level=LogLevel.DEBUG)
        assert len(entries) == 2
        assert entries[0].content == "Parent message"
        assert entries[1].content == child_manager

    def test_collect_entries_with_flattening(self):
        """Test _collect_entries with flattening enabled."""
        parent_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager.add("Child message", LogLevel.INFO, formatinfo=None, realtime=False)

        parent_manager.add("Parent message", LogLevel.INFO, formatinfo=None, realtime=False)
        parent_manager.add(child_manager, LogLevel.INFO, formatinfo=None, realtime=False)

        # Test with flattening
        entries = parent_manager._collect_entries(flatten=True, sort=False, level=LogLevel.DEBUG)
        assert len(entries) == 2
        assert entries[0].content == "Parent message"
        assert entries[1].content == "Child message"

    def test_collect_entries_with_sorting(self):
        """Test _collect_entries with sorting enabled."""
        manager = OutputManager(name=None, level=LogLevel.DEBUG)

        # Add entries with different timestamps
        from src.infrastructure.drivers.logging.types import LogEntry
        entry1 = LogEntry("Second message", LogLevel.INFO, datetime(2023, 1, 1, 12, 0, 0))
        entry2 = LogEntry("First message", LogLevel.INFO, datetime(2023, 1, 1, 11, 0, 0))

        manager.entries = [entry1, entry2]

        # Without sorting
        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.DEBUG)
        assert entries[0].content == "Second message"
        assert entries[1].content == "First message"

        # With sorting
        entries = manager._collect_entries(flatten=False, sort=True, level=LogLevel.DEBUG)
        assert entries[0].content == "First message"
        assert entries[1].content == "Second message"

    def test_output_without_name(self):
        """Test output method without manager name."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        result = manager.output(indent=0, level=LogLevel.DEBUG)
        lines = result.split('\n')
        assert len(lines) == 1
        assert "Test message" in lines[0]

    def test_output_with_name(self):
        """Test output method with manager name."""
        manager = OutputManager(name="TestLogger", level=LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        result = manager.output(indent=0, level=LogLevel.DEBUG)
        lines = result.split('\n')
        assert len(lines) == 2
        assert lines[0] == "TestLogger"
        assert "Test message" in lines[1]

    def test_output_with_indent(self):
        """Test output method with indentation."""
        manager = OutputManager(name="TestLogger", level=LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        result = manager.output(indent=2, level=LogLevel.DEBUG)
        lines = result.split('\n')
        assert lines[0] == "        TestLogger"  # 8 spaces (2 * 4)

    def test_output_with_level_filter(self):
        """Test output method with level filtering."""
        manager = OutputManager(name=None, level=LogLevel.DEBUG)
        manager.add("Debug message", LogLevel.DEBUG, formatinfo=None, realtime=False)
        manager.add("Info message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Error message", LogLevel.ERROR, formatinfo=None, realtime=False)

        result = manager.output(indent=0, level=LogLevel.INFO)
        lines = result.split('\n')
        assert len(lines) == 2
        assert "Info message" in lines[0]
        assert "Error message" in lines[1]

    @patch('builtins.print')
    def test_flush(self, mock_print):
        """Test flush method."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        manager.flush()
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert "Test message" in args[0]

    def test_flatten(self):
        """Test flatten method."""
        parent_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager = OutputManager(name=None, level=LogLevel.INFO)
        child_manager.add("Child message", LogLevel.INFO, formatinfo=None, realtime=False)

        parent_manager.add("Parent message", LogLevel.INFO, formatinfo=None, realtime=False)
        parent_manager.add(child_manager, LogLevel.INFO, formatinfo=None, realtime=False)

        flattened = parent_manager.flatten(level=LogLevel.DEBUG)
        assert len(flattened) == 2
        assert flattened[0].content == "Parent message"
        assert flattened[1].content == "Child message"

    def test_flatten_with_level_filter(self):
        """Test flatten method with level filtering."""
        manager = OutputManager(name=None, level=LogLevel.DEBUG)
        manager.add("Debug message", LogLevel.DEBUG, formatinfo=None, realtime=False)
        manager.add("Info message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Error message", LogLevel.ERROR, formatinfo=None, realtime=False)

        flattened = manager.flatten(level=LogLevel.INFO)
        assert len(flattened) == 2
        assert flattened[0].content == "Info message"
        assert flattened[1].content == "Error message"

    def test_output_sorted(self):
        """Test output_sorted method."""
        manager = OutputManager(name=None, level=LogLevel.DEBUG)

        # Add entries with different timestamps
        from src.infrastructure.drivers.logging.types import LogEntry
        entry1 = LogEntry("Second message", LogLevel.INFO, datetime(2023, 1, 1, 12, 0, 0))
        entry2 = LogEntry("First message", LogLevel.INFO, datetime(2023, 1, 1, 11, 0, 0))

        manager.entries = [entry1, entry2]

        result = manager.output_sorted(level=LogLevel.DEBUG)
        lines = result.split('\n')
        assert "First message" in lines[0]
        assert "Second message" in lines[1]

    def test_output_sorted_with_level_filter(self):
        """Test output_sorted method with level filtering."""
        manager = OutputManager(name=None, level=LogLevel.DEBUG)

        from src.infrastructure.drivers.logging.types import LogEntry
        entry1 = LogEntry("Debug message", LogLevel.DEBUG, datetime(2023, 1, 1, 12, 0, 0))
        entry2 = LogEntry("Info message", LogLevel.INFO, datetime(2023, 1, 1, 11, 0, 0))

        manager.entries = [entry1, entry2]

        result = manager.output_sorted(level=LogLevel.INFO)
        lines = result.split('\n')
        assert len(lines) == 1
        assert "Info message" in lines[0]

    def test_complex_nested_structure(self):
        """Test complex nested OutputManager structure."""
        root = OutputManager(name="Root", level=LogLevel.INFO)
        child1 = OutputManager(name="Child1", level=LogLevel.INFO)
        child2 = OutputManager(name="Child2", level=LogLevel.INFO)
        grandchild = OutputManager(name="Grandchild", level=LogLevel.INFO)

        grandchild.add("Grandchild message", LogLevel.INFO, formatinfo=None, realtime=False)
        child1.add("Child1 message", LogLevel.INFO, formatinfo=None, realtime=False)
        child1.add(grandchild, LogLevel.INFO, formatinfo=None, realtime=False)
        child2.add("Child2 message", LogLevel.INFO, formatinfo=None, realtime=False)

        root.add(child1, LogLevel.INFO, formatinfo=None, realtime=False)
        root.add(child2, LogLevel.INFO, formatinfo=None, realtime=False)

        # Test flattening
        flattened = root.flatten(level=LogLevel.DEBUG)
        assert len(flattened) == 3
        assert flattened[0].content == "Child1 message"
        assert flattened[1].content == "Grandchild message"
        assert flattened[2].content == "Child2 message"

    def test_empty_manager_output(self):
        """Test output of empty manager."""
        manager = OutputManager(name=None, level=LogLevel.INFO)
        result = manager.output(indent=0, level=LogLevel.DEBUG)
        assert result == ""

    def test_empty_manager_with_name_output(self):
        """Test output of empty manager with name."""
        manager = OutputManager(name="EmptyLogger", level=LogLevel.INFO)
        result = manager.output(indent=0, level=LogLevel.DEBUG)
        assert result == "EmptyLogger"
