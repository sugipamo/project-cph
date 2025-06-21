"""Tests for MockOutputManager."""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.interfaces.output_manager_interface import OutputManagerInterface
from src.infrastructure.drivers.logging.mock_output_manager import MockOutputManager
from src.infrastructure.drivers.logging.types import LogLevel


class TestMockOutputManager:
    """Test cases for MockOutputManager."""

    def test_init_default(self):
        """Test MockOutputManager initialization with defaults."""
        manager = MockOutputManager(name=None, level=LogLevel.INFO)

        assert manager.name is None
        assert manager.level == LogLevel.INFO
        assert manager.entries == []
        assert manager.captured_outputs == []
        assert manager.flush_calls == 0

    def test_init_with_parameters(self):
        """Test MockOutputManager initialization with parameters."""
        manager = MockOutputManager(name="test-manager", level=LogLevel.DEBUG)

        assert manager.name == "test-manager"
        assert manager.level == LogLevel.DEBUG
        assert manager.entries == []
        assert manager.captured_outputs == []
        assert manager.flush_calls == 0

    def test_init_with_config_manager(self):
        """Test MockOutputManager initialization with config manager."""
        mock_config_manager = Mock()

        with patch('src.infrastructure.drivers.logging.mock_output_manager.DIContainer') as mock_container:
            mock_container.resolve.return_value = mock_config_manager

            manager = MockOutputManager(name=None, level=LogLevel.INFO)

            assert manager._config_manager == mock_config_manager

    def test_init_without_config_manager(self):
        """Test MockOutputManager initialization when config manager fails."""
        with patch('src.infrastructure.drivers.logging.mock_output_manager.DIContainer') as mock_container:
            mock_container.resolve.side_effect = Exception("Config not found")

            manager = MockOutputManager(name=None, level=LogLevel.INFO)

            # manager already initialized above

            assert manager._config_manager is None

    def test_add_simple_message(self):
        """Test adding simple string message."""
        manager = MockOutputManager(name=None, level=LogLevel.INFO)

        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        assert len(manager.entries) == 1
        assert manager.entries[0].content == "Test message"
        assert manager.entries[0].level == LogLevel.INFO

    def test_add_with_format_info(self):
        """Test adding message with format info."""
        manager = MockOutputManager(name=None, level=LogLevel.INFO)
        format_info = FormatInfo(color="red")

        manager.add("Test message", LogLevel.ERROR, formatinfo=format_info, realtime=False)

        assert len(manager.entries) == 1
        assert manager.entries[0].content == "Test message"
        assert manager.entries[0].level == LogLevel.ERROR
        assert manager.entries[0].formatinfo == format_info

    def test_add_realtime_string_message(self):
        """Test adding string message with realtime flag."""
        manager = MockOutputManager(name=None, level=LogLevel.INFO)
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.return_value = "default_text"
        manager._config_manager = mock_config_manager

        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=True)

        assert len(manager.entries) == 1
        assert len(manager.captured_outputs) == 1
        assert manager.captured_outputs[0] == "Test message"

    def test_add_realtime_output_manager_message(self):
        """Test adding OutputManager message with realtime flag."""
        manager = MockOutputManager(name=None, level=LogLevel.INFO)

        # Mock another OutputManager that implements OutputManagerInterface
        mock_output_manager = Mock(spec=OutputManagerInterface)
        mock_output_manager.output.return_value = "nested output"

        manager.add(mock_output_manager, LogLevel.INFO, formatinfo=None, realtime=True)

        assert len(manager.entries) == 1
        assert len(manager.captured_outputs) == 1
        assert manager.captured_outputs[0] == "nested output"




    def test_should_log(self):
        """Test _should_log method."""
        manager = MockOutputManager(name=None, level=LogLevel.INFO)

        assert manager._should_log(LogLevel.DEBUG) is False
        assert manager._should_log(LogLevel.INFO) is True
        assert manager._should_log(LogLevel.WARNING) is True
        assert manager._should_log(LogLevel.ERROR) is True

    def test_collect_entries_basic(self):
        """Test _collect_entries method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.add("Debug message", LogLevel.DEBUG, formatinfo=None, realtime=False)
        manager.add("Info message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Error message", LogLevel.ERROR, formatinfo=None, realtime=False)

        # Collect all entries
        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.DEBUG)
        assert len(entries) == 3

        # Collect only INFO and above
        entries = manager._collect_entries(flatten=False, sort=False, level=LogLevel.INFO)
        assert len(entries) == 2
        assert entries[0].content == "Info message"
        assert entries[1].content == "Error message"

    def test_collect_entries_with_sort(self):
        """Test _collect_entries with sorting."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        # Add entries (they'll have different timestamps)
        manager.add("First message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Second message", LogLevel.INFO, formatinfo=None, realtime=False)

        entries = manager._collect_entries(flatten=False, sort=True, level=LogLevel.DEBUG)
        assert len(entries) == 2
        # Should be sorted by timestamp
        assert entries[0].timestamp <= entries[1].timestamp

    def test_output_basic(self):
        """Test output method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.add("Test message 1", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Test message 2", LogLevel.ERROR, formatinfo=None, realtime=False)

        output = manager.output(indent=0, level=LogLevel.DEBUG)

        # Should contain both messages
        assert "Test message 1" in output
        assert "Test message 2" in output

    def test_output_with_name(self):
        """Test output method with manager name."""
        manager = MockOutputManager(name="test-manager", level=LogLevel.DEBUG)

        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        output = manager.output(indent=0, level=LogLevel.DEBUG)

        assert "test-manager" in output
        assert "Test message" in output

    def test_output_with_indent(self):
        """Test output method with indentation."""
        manager = MockOutputManager(name="test-manager", level=LogLevel.DEBUG)

        output = manager.output(indent=2, level=LogLevel.DEBUG)

        assert output.startswith("        test-manager")  # 2 * 4 spaces

    def test_output_with_level_filter(self):
        """Test output method with level filtering."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.add("Debug message", LogLevel.DEBUG, formatinfo=None, realtime=False)
        manager.add("Info message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Error message", LogLevel.ERROR, formatinfo=None, realtime=False)

        output = manager.output(indent=0, level=LogLevel.INFO)

        assert "Debug message" not in output
        assert "Info message" in output
        assert "Error message" in output

    def test_flush(self):
        """Test flush method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.add("Test message", LogLevel.INFO, formatinfo=None, realtime=False)

        initial_flush_calls = manager.flush_calls
        initial_outputs = len(manager.captured_outputs)

        manager.flush()

        assert manager.flush_calls == initial_flush_calls + 1
        assert len(manager.captured_outputs) == initial_outputs + 1

    def test_flatten(self):
        """Test flatten method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.add("Debug message", LogLevel.DEBUG, formatinfo=None, realtime=False)
        manager.add("Info message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Error message", LogLevel.ERROR, formatinfo=None, realtime=False)

        # Get all entries flattened
        flattened = manager.flatten(level=LogLevel.DEBUG)
        assert len(flattened) == 3

        # Get only INFO and above
        flattened = manager.flatten(level=LogLevel.INFO)
        assert len(flattened) == 2

    def test_output_sorted(self):
        """Test output_sorted method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.add("Message 1", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Message 2", LogLevel.ERROR, formatinfo=None, realtime=False)

        sorted_output = manager.output_sorted(level=LogLevel.DEBUG)

        assert "Message 1" in sorted_output
        assert "Message 2" in sorted_output

    def test_get_captured_outputs(self):
        """Test get_captured_outputs utility method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.captured_outputs.append("Test output 1")
        manager.captured_outputs.append("Test output 2")

        captured = manager.get_captured_outputs()

        assert len(captured) == 2
        assert captured[0] == "Test output 1"
        assert captured[1] == "Test output 2"

        # Should return a copy, not the original list
        captured.append("Modified")
        assert len(manager.captured_outputs) == 2

    def test_get_flush_count(self):
        """Test get_flush_count utility method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        assert manager.get_flush_count() == 0

        manager.flush()
        assert manager.get_flush_count() == 1

        manager.flush()
        assert manager.get_flush_count() == 2

    def test_clear_captured(self):
        """Test clear_captured utility method."""
        manager = MockOutputManager(name=None, level=LogLevel.DEBUG)

        manager.captured_outputs.append("Test output")
        manager.flush()

        assert len(manager.captured_outputs) > 0
        assert manager.flush_calls > 0

        manager.clear_captured()

        assert len(manager.captured_outputs) == 0
        assert manager.flush_calls == 0

    def test_multiple_operations(self):
        """Test multiple operations working together."""
        manager = MockOutputManager(name="test-manager", level=LogLevel.INFO)

        # Add various messages
        manager.add("Debug message", LogLevel.DEBUG, formatinfo=None, realtime=False)  # Should be filtered out
        manager.add("Info message", LogLevel.INFO, formatinfo=None, realtime=False)
        manager.add("Warning message", LogLevel.WARNING, formatinfo=None, realtime=False)
        manager.add("Error message", LogLevel.ERROR, formatinfo=None, realtime=False)

        # Test output filtering
        output = manager.output(indent=0, level=LogLevel.INFO)
        assert "Debug message" not in output
        assert "Info message" in output
        assert "Warning message" in output
        assert "Error message" in output

        # Test flush
        manager.flush()
        assert manager.get_flush_count() == 1
        assert len(manager.get_captured_outputs()) == 1

        # Test flatten
        flattened = manager.flatten(level=LogLevel.WARNING)
        assert len(flattened) == 2  # WARNING and ERROR

        # Test clear
        manager.clear_captured()
        assert len(manager.get_captured_outputs()) == 0
        assert manager.get_flush_count() == 0
