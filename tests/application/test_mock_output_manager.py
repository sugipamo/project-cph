"""Tests for MockOutputManager."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.application.mock_output_manager import MockOutputManager
from src.utils.types import LogEntry, LogLevel
from src.utils.format_info import FormatInfo


class TestMockOutputManager:
    """Test MockOutputManager functionality."""

    def test_initialization(self):
        """Test MockOutputManager initialization."""
        manager = MockOutputManager("test_manager", LogLevel.INFO)
        assert manager.name == "test_manager"
        assert manager.level == LogLevel.INFO
        assert manager.entries == []
        assert manager.captured_outputs == []
        assert manager.flush_calls == 0

    def test_initialization_without_name(self):
        """Test MockOutputManager initialization without name."""
        manager = MockOutputManager(None, LogLevel.DEBUG)
        assert manager.name is None
        assert manager.level == LogLevel.DEBUG

    def test_add_string_message(self):
        """Test adding string message."""
        manager = MockOutputManager("test", LogLevel.INFO)
        manager.add("Test message", LogLevel.INFO, None, False)
        
        assert len(manager.entries) == 1
        assert manager.entries[0].content == "Test message"
        assert manager.entries[0].level == LogLevel.INFO
        assert len(manager.captured_outputs) == 0  # realtime=False

    def test_add_with_realtime(self):
        """Test adding message with realtime=True."""
        manager = MockOutputManager("test", LogLevel.INFO)
        manager.add("Realtime message", LogLevel.INFO, None, True)
        
        assert len(manager.entries) == 1
        assert len(manager.captured_outputs) == 1
        assert manager.captured_outputs[0] == "Realtime message"

    def test_add_output_manager_interface_with_realtime(self):
        """Test adding OutputManagerInterface object with realtime=True."""
        manager = MockOutputManager("test", LogLevel.INFO)
        
        # Mock an OutputManagerInterface object
        mock_output_obj = Mock()
        mock_output_obj.output.return_value = "Mock output"
        
        manager.add(mock_output_obj, LogLevel.INFO, None, True)
        
        assert len(manager.entries) == 1
        assert len(manager.captured_outputs) == 1
        assert manager.captured_outputs[0] == "Mock output"
        mock_output_obj.output.assert_called_once()

    def test_add_with_config_manager_error(self):
        """Test adding message when config manager raises error."""
        manager = MockOutputManager("test", LogLevel.INFO)
        manager._config_manager = Mock()
        manager._config_manager.resolve_config.side_effect = KeyError("Config not found")
        
        with pytest.raises(ValueError, match="Mock output default text configuration not found"):
            manager.add("", LogLevel.INFO, None, True)

    def test_add_with_format_info(self):
        """Test adding message with FormatInfo."""
        manager = MockOutputManager("test", LogLevel.INFO)
        format_info = FormatInfo(indent=2, prefix=">>", suffix="<<")
        
        manager.add("Formatted message", LogLevel.WARNING, format_info, False)
        
        assert len(manager.entries) == 1
        assert manager.entries[0].formatinfo == format_info

    def test_should_log(self):
        """Test _should_log method."""
        manager = MockOutputManager("test", LogLevel.INFO)
        
        assert manager._should_log(LogLevel.ERROR) is True
        assert manager._should_log(LogLevel.WARNING) is True
        assert manager._should_log(LogLevel.INFO) is True
        assert manager._should_log(LogLevel.DEBUG) is False

    def test_collect_entries_basic(self):
        """Test _collect_entries with basic entries."""
        manager = MockOutputManager("test", LogLevel.DEBUG)
        
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

    def test_collect_entries_with_sort(self):
        """Test _collect_entries with sorting."""
        manager = MockOutputManager("test", LogLevel.DEBUG)
        
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
        manager = MockOutputManager("TestManager", LogLevel.INFO)
        
        manager.add("Info message", LogLevel.INFO, None, False)
        manager.add("Debug message", LogLevel.DEBUG, None, False)  # Should be filtered out
        manager.add("Error message", LogLevel.ERROR, None, False)
        
        output = manager.output(indent=0, level=LogLevel.INFO)
        lines = output.split('\n')
        
        assert lines[0] == "TestManager"
        assert len(lines) == 3  # Name + 2 messages (debug filtered out)

    def test_output_with_indent(self):
        """Test output generation with indentation."""
        manager = MockOutputManager("IndentedManager", LogLevel.INFO)
        manager.add("Message", LogLevel.INFO, None, False)
        
        output = manager.output(indent=2, level=LogLevel.INFO)
        lines = output.split('\n')
        
        assert lines[0] == "        IndentedManager"  # 4 spaces * 2 = 8 spaces

    def test_output_without_name(self):
        """Test output generation without manager name."""
        manager = MockOutputManager(None, LogLevel.INFO)
        manager.add("Message", LogLevel.INFO, None, False)
        
        output = manager.output(indent=0, level=LogLevel.INFO)
        lines = output.split('\n')
        
        assert len(lines) == 1  # Only the message, no name

    def test_flush(self):
        """Test flush functionality."""
        manager = MockOutputManager("test", LogLevel.INFO)
        manager.add("Message 1", LogLevel.INFO, None, False)
        manager.add("Message 2", LogLevel.INFO, None, False)
        
        assert manager.flush_calls == 0
        assert len(manager.captured_outputs) == 0
        
        manager.flush()
        
        assert manager.flush_calls == 1
        assert len(manager.captured_outputs) == 1
        assert "test" in manager.captured_outputs[0]
        assert "Message 1" in manager.captured_outputs[0]
        assert "Message 2" in manager.captured_outputs[0]

    def test_flatten(self):
        """Test flatten functionality."""
        manager = MockOutputManager("test", LogLevel.DEBUG)
        
        manager.add("Debug", LogLevel.DEBUG, None, False)
        manager.add("Info", LogLevel.INFO, None, False)
        manager.add("Warning", LogLevel.WARNING, None, False)
        
        # Flatten with DEBUG level
        entries = manager.flatten(LogLevel.DEBUG)
        assert len(entries) == 3
        
        # Flatten with INFO level
        entries = manager.flatten(LogLevel.INFO)
        assert len(entries) == 2

    def test_output_sorted(self):
        """Test output_sorted functionality."""
        manager = MockOutputManager("test", LogLevel.INFO)
        
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

    def test_get_captured_outputs(self):
        """Test get_captured_outputs functionality."""
        manager = MockOutputManager("test", LogLevel.INFO)
        
        manager.add("Message 1", LogLevel.INFO, None, True)
        manager.add("Message 2", LogLevel.INFO, None, True)
        
        outputs = manager.get_captured_outputs()
        assert len(outputs) == 2
        assert outputs[0] == "Message 1"
        assert outputs[1] == "Message 2"
        
        # Verify it returns a copy
        outputs.append("Modified")
        assert len(manager.captured_outputs) == 2

    def test_get_flush_count(self):
        """Test get_flush_count functionality."""
        manager = MockOutputManager("test", LogLevel.INFO)
        
        assert manager.get_flush_count() == 0
        
        manager.flush()
        assert manager.get_flush_count() == 1
        
        manager.flush()
        manager.flush()
        assert manager.get_flush_count() == 3

    def test_clear_captured(self):
        """Test clear_captured functionality."""
        manager = MockOutputManager("test", LogLevel.INFO)
        
        manager.add("Message", LogLevel.INFO, None, True)
        manager.flush()
        manager.flush()
        
        assert len(manager.captured_outputs) == 3  # 1 from add, 2 from flush
        assert manager.flush_calls == 2
        
        manager.clear_captured()
        
        assert len(manager.captured_outputs) == 0
        assert manager.flush_calls == 0