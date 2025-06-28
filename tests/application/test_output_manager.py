"""Tests for OutputManager."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from io import StringIO

from src.application.output_manager import OutputManager
from src.utils.types import LogEntry, LogLevel
from src.utils.format_info import FormatInfo


class TestOutputManager:
    """Test OutputManager functionality."""

    def test_initialization(self):
        """Test OutputManager initialization."""
        manager = OutputManager("test_manager", LogLevel.INFO)
        assert manager.name == "test_manager"
        assert manager.level == LogLevel.INFO
        assert manager.entries == []

    def test_initialization_without_name(self):
        """Test OutputManager initialization without name."""
        manager = OutputManager(None, LogLevel.DEBUG)
        assert manager.name is None
        assert manager.level == LogLevel.DEBUG

    def test_add_string_message(self):
        """Test adding string message."""
        manager = OutputManager("test", LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, None, False)
        
        assert len(manager.entries) == 1
        assert manager.entries[0].content == "Test message"
        assert manager.entries[0].level == LogLevel.INFO

    @patch('builtins.print')
    def test_add_with_realtime(self, mock_print):
        """Test adding message with realtime=True."""
        manager = OutputManager("test", LogLevel.INFO)
        manager.add("Realtime message", LogLevel.INFO, None, True)
        
        assert len(manager.entries) == 1
        mock_print.assert_called_once_with("Realtime message")

    @patch('builtins.print')
    def test_add_output_manager_with_realtime(self, mock_print):
        """Test adding OutputManager object with realtime=True."""
        manager = OutputManager("test", LogLevel.INFO)
        
        # Create another OutputManager to add
        child_manager = OutputManager("child", LogLevel.INFO)
        child_manager.add("Child message", LogLevel.INFO, None, False)
        
        manager.add(child_manager, LogLevel.INFO, None, True)
        
        assert len(manager.entries) == 1
        mock_print.assert_called_once()
        # Verify it calls output method on child
        call_args = mock_print.call_args[0][0]
        assert "child" in call_args
        assert "Child message" in call_args

    def test_add_with_format_info(self):
        """Test adding message with FormatInfo."""
        manager = OutputManager("test", LogLevel.INFO)
        format_info = FormatInfo(indent=2, prefix=">>", suffix="<<")
        
        manager.add("Formatted message", LogLevel.WARNING, format_info, False)
        
        assert len(manager.entries) == 1
        assert manager.entries[0].formatinfo == format_info

    def test_should_log(self):
        """Test _should_log method."""
        manager = OutputManager("test", LogLevel.INFO)
        
        assert manager._should_log(LogLevel.ERROR) is True
        assert manager._should_log(LogLevel.WARNING) is True
        assert manager._should_log(LogLevel.INFO) is True
        assert manager._should_log(LogLevel.DEBUG) is False

    def test_collect_entries_basic(self):
        """Test _collect_entries with basic entries."""
        manager = OutputManager("test", LogLevel.DEBUG)
        
        manager.add("Debug message", LogLevel.DEBUG, None, False)
        manager.add("Info message", LogLevel.INFO, None, False)
        manager.add("Warning message", LogLevel.WARNING, None, False)
        manager.add("Error message", LogLevel.ERROR, None, False)
        
        # Collect all entries
        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.DEBUG)
        assert len(entries) == 4
        
        # Collect only INFO and above
        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.INFO)
        assert len(entries) == 3
        
        # Collect only ERROR
        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.ERROR)
        assert len(entries) == 1

    def test_collect_entries_with_nested_managers(self):
        """Test _collect_entries with nested OutputManagers (flatten=True)."""
        manager = OutputManager("parent", LogLevel.DEBUG)
        
        # Create child managers
        child1 = OutputManager("child1", LogLevel.DEBUG)
        child1.add("Child1 message", LogLevel.INFO, None, False)
        
        child2 = OutputManager("child2", LogLevel.DEBUG)
        child2.add("Child2 message", LogLevel.WARNING, None, False)
        
        # Add child managers to parent
        manager.add(child1, LogLevel.INFO, None, False)
        manager.add(child2, LogLevel.INFO, None, False)
        manager.add("Parent message", LogLevel.ERROR, None, False)
        
        # Collect without flatten
        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.DEBUG)
        assert len(entries) == 3  # 2 child managers + 1 parent message
        
        # Collect with flatten
        entries = manager._collect_entries(flatten=True, sort=False, level=LogLevel.DEBUG)
        assert len(entries) == 3  # All individual messages flattened

    def test_collect_entries_with_sort(self):
        """Test _collect_entries with sorting."""
        manager = OutputManager("test", LogLevel.DEBUG)
        
        # Add entries with different timestamps
        with patch('src.utils.types.datetime') as mock_datetime:
            mock_datetime.now.side_effect = [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 10, 0, 1),
                datetime(2024, 1, 1, 10, 0, 2),
            ]
            manager.add("First", LogLevel.INFO, None, False)
            manager.add("Second", LogLevel.INFO, None, False)
            manager.add("Third", LogLevel.INFO, None, False)
        
        entries = manager._collect_entries(flatten=False, sort=True, level=LogLevel.DEBUG)
        assert len(entries) == 3
        # Verify they're sorted by timestamp
        assert entries[0].content == "First"
        assert entries[1].content == "Second"
        assert entries[2].content == "Third"

    def test_output(self):
        """Test output generation."""
        manager = OutputManager("TestManager", LogLevel.INFO)
        
        manager.add("Info message", LogLevel.INFO, None, False)
        manager.add("Debug message", LogLevel.DEBUG, None, False)  # Should be filtered out
        manager.add("Error message", LogLevel.ERROR, None, False)
        
        output = manager.output(indent=0, level=LogLevel.INFO)
        lines = output.split('\n')
        
        assert lines[0] == "TestManager"
        assert len(lines) == 3  # Name + 2 messages (debug filtered out)

    def test_output_with_indent(self):
        """Test output generation with indentation."""
        manager = OutputManager("IndentedManager", LogLevel.INFO)
        manager.add("Message", LogLevel.INFO, None, False)
        
        output = manager.output(indent=2, level=LogLevel.INFO)
        lines = output.split('\n')
        
        assert lines[0] == "        IndentedManager"  # 4 spaces * 2 = 8 spaces

    def test_output_without_name(self):
        """Test output generation without manager name."""
        manager = OutputManager(None, LogLevel.INFO)
        manager.add("Message", LogLevel.INFO, None, False)
        
        output = manager.output(indent=0, level=LogLevel.INFO)
        lines = output.split('\n')
        
        assert len(lines) == 1  # Only the message, no name

    @patch('builtins.print')
    def test_flush(self, mock_print):
        """Test flush functionality."""
        manager = OutputManager("test", LogLevel.INFO)
        manager.add("Message 1", LogLevel.INFO, None, False)
        manager.add("Message 2", LogLevel.INFO, None, False)
        
        manager.flush()
        
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        assert "test" in output
        assert "Message 1" in output
        assert "Message 2" in output

    def test_flatten(self):
        """Test flatten functionality."""
        manager = OutputManager("test", LogLevel.DEBUG)
        
        # Create nested structure
        child = OutputManager("child", LogLevel.DEBUG)
        child.add("Child message", LogLevel.INFO, None, False)
        
        manager.add("Direct message", LogLevel.INFO, None, False)
        manager.add(child, LogLevel.INFO, None, False)
        
        # Flatten with DEBUG level
        entries = manager.flatten(LogLevel.DEBUG)
        assert len(entries) == 2  # Direct message + child's message (flattened)

    def test_output_sorted(self):
        """Test output_sorted functionality."""
        manager = OutputManager("test", LogLevel.INFO)
        
        with patch('src.utils.types.datetime') as mock_datetime:
            mock_datetime.now.side_effect = [
                datetime(2024, 1, 1, 10, 0, 2),
                datetime(2024, 1, 1, 10, 0, 1),
                datetime(2024, 1, 1, 10, 0, 3),
            ]
            manager.add("Second", LogLevel.INFO, None, False)
            manager.add("First", LogLevel.INFO, None, False)
            manager.add("Third", LogLevel.INFO, None, False)
        
        output = manager.output_sorted(LogLevel.INFO)
        lines = output.split('\n')
        
        # Verify messages are in chronological order
        assert "First" in lines[0]
        assert "Second" in lines[1]
        assert "Third" in lines[2]

    def test_set_level(self):
        """Test set_level functionality."""
        manager = OutputManager("test", LogLevel.INFO)
        
        assert manager.level == LogLevel.INFO
        
        manager.set_level(LogLevel.DEBUG)
        assert manager.level == LogLevel.DEBUG
        
        manager.set_level(LogLevel.ERROR)
        assert manager.level == LogLevel.ERROR

    def test_get_level(self):
        """Test get_level functionality."""
        manager = OutputManager("test", LogLevel.WARNING)
        
        assert manager.get_level() == LogLevel.WARNING
        
        manager.level = LogLevel.DEBUG
        assert manager.get_level() == LogLevel.DEBUG

    def test_level_filtering_after_set_level(self):
        """Test that level filtering works correctly after changing level."""
        manager = OutputManager("test", LogLevel.INFO)
        
        # Add messages at different levels
        manager.add("Debug 1", LogLevel.DEBUG, None, False)
        manager.add("Info 1", LogLevel.INFO, None, False)
        manager.add("Warning 1", LogLevel.WARNING, None, False)
        
        # Initially should not include DEBUG
        output = manager.output(0, LogLevel.INFO)
        assert "Debug 1" not in output
        assert "Info 1" in output
        assert "Warning 1" in output
        
        # Change level to DEBUG
        manager.set_level(LogLevel.DEBUG)
        
        # Now DEBUG messages should be included
        output = manager.output(0, LogLevel.DEBUG)
        assert "Debug 1" in output
        assert "Info 1" in output
        assert "Warning 1" in output