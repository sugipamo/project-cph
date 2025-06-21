"""Tests for MockOutputManager."""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.mock_output_manager import MockOutputManager
from src.infrastructure.drivers.logging.types import LogLevel


class TestMockOutputManager:
    """Test cases for MockOutputManager."""

    def test_init_default(self):
        """Test MockOutputManager initialization with defaults."""
        manager = MockOutputManager()

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

            manager = MockOutputManager()

            assert manager._config_manager == mock_config_manager

    def test_init_without_config_manager(self):
        """Test MockOutputManager initialization when config manager fails."""
        with patch('src.infrastructure.drivers.logging.mock_output_manager.DIContainer') as mock_container:
            mock_container.resolve.side_effect = Exception("Config not found")

            manager = MockOutputManager()

            assert manager._config_manager is None

    def test_add_simple_message(self):
        """Test adding simple string message."""
        manager = MockOutputManager()

        manager.add("Test message", LogLevel.INFO)

        assert len(manager.entries) == 1
        assert manager.entries[0].content == "Test message"
        assert manager.entries[0].level == LogLevel.INFO

    def test_add_with_format_info(self):
        """Test adding message with format info."""
        manager = MockOutputManager()
        format_info = FormatInfo(color="red")

        manager.add("Test message", LogLevel.ERROR, formatinfo=format_info)

        assert len(manager.entries) == 1
        assert manager.entries[0].content == "Test message"
        assert manager.entries[0].level == LogLevel.ERROR
        assert manager.entries[0].formatinfo == format_info

    def test_add_realtime_string_message(self):
        """Test adding string message with realtime flag."""
        manager = MockOutputManager()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.return_value = "default_text"
        manager._config_manager = mock_config_manager

        manager.add("Test message", LogLevel.INFO, realtime=True)

        assert len(manager.entries) == 1
        assert len(manager.captured_outputs) == 1
        assert manager.captured_outputs[0] == "Test message"

    def test_add_realtime_output_manager_message(self):
        """Test adding OutputManager message with realtime flag."""
        manager = MockOutputManager()

        # Mock another OutputManager
        mock_output_manager = Mock()
        mock_output_manager.output.return_value = "nested output"

        manager.add(mock_output_manager, LogLevel.INFO, realtime=True)

        assert len(manager.entries) == 1
        assert len(manager.captured_outputs) == 1
        assert manager.captured_outputs[0] == "nested output"

    def test_add_realtime_no_config_manager(self):
        """Test adding realtime message when config manager not available."""
        manager = MockOutputManager()
        manager._config_manager = None

        with pytest.raises(ValueError, match="Mock output default text configuration not found"):
            manager.add("Test message", LogLevel.INFO, realtime=True)

    def test_add_realtime_config_error(self):
        """Test adding realtime message when config resolution fails."""
        manager = MockOutputManager()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = KeyError("Config not found")
        manager._config_manager = mock_config_manager

        with pytest.raises(ValueError, match="Mock output default text configuration not found"):
            manager.add("Test message", LogLevel.INFO, realtime=True)

    def test_add_realtime_empty_message(self):
        """Test adding empty realtime message."""
        manager = MockOutputManager()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = KeyError("No default")
        manager._config_manager = mock_config_manager

        with pytest.raises(ValueError, match="Mock output default text configuration not found"):
            manager.add("", LogLevel.INFO, realtime=True)

    def test_should_log(self):
        """Test _should_log method."""
        manager = MockOutputManager(level=LogLevel.INFO)

        assert manager._should_log(LogLevel.DEBUG) is False
        assert manager._should_log(LogLevel.INFO) is True
        assert manager._should_log(LogLevel.WARNING) is True
        assert manager._should_log(LogLevel.ERROR) is True

    def test_collect_entries_basic(self):
        """Test _collect_entries method."""
        manager = MockOutputManager()

        manager.add("Debug message", LogLevel.DEBUG)
        manager.add("Info message", LogLevel.INFO)
        manager.add("Error message", LogLevel.ERROR)

        # Collect all entries
        entries = manager._collect_entries(level=LogLevel.DEBUG)
        assert len(entries) == 3

        # Collect only INFO and above
        entries = manager._collect_entries(level=LogLevel.INFO)
        assert len(entries) == 2
        assert entries[0].content == "Info message"
        assert entries[1].content == "Error message"

    def test_collect_entries_with_sort(self):
        """Test _collect_entries with sorting."""
        manager = MockOutputManager()

        # Add entries (they'll have different timestamps)
        manager.add("First message", LogLevel.INFO)
        manager.add("Second message", LogLevel.INFO)

        entries = manager._collect_entries(sort=True)
        assert len(entries) == 2
        # Should be sorted by timestamp
        assert entries[0].timestamp <= entries[1].timestamp

    def test_output_basic(self):
        """Test output method."""
        manager = MockOutputManager()

        manager.add("Test message 1", LogLevel.INFO)
        manager.add("Test message 2", LogLevel.ERROR)

        output = manager.output()

        # Should contain both messages
        assert "Test message 1" in output
        assert "Test message 2" in output

    def test_output_with_name(self):
        """Test output method with manager name."""
        manager = MockOutputManager(name="test-manager")

        manager.add("Test message", LogLevel.INFO)

        output = manager.output()

        assert "test-manager" in output
        assert "Test message" in output

    def test_output_with_indent(self):
        """Test output method with indentation."""
        manager = MockOutputManager(name="test-manager")

        output = manager.output(indent=2)

        assert output.startswith("        test-manager")  # 2 * 4 spaces

    def test_output_with_level_filter(self):
        """Test output method with level filtering."""
        manager = MockOutputManager()

        manager.add("Debug message", LogLevel.DEBUG)
        manager.add("Info message", LogLevel.INFO)
        manager.add("Error message", LogLevel.ERROR)

        output = manager.output(level=LogLevel.INFO)

        assert "Debug message" not in output
        assert "Info message" in output
        assert "Error message" in output

    def test_flush(self):
        """Test flush method."""
        manager = MockOutputManager()

        manager.add("Test message", LogLevel.INFO)

        initial_flush_calls = manager.flush_calls
        initial_outputs = len(manager.captured_outputs)

        manager.flush()

        assert manager.flush_calls == initial_flush_calls + 1
        assert len(manager.captured_outputs) == initial_outputs + 1

    def test_flatten(self):
        """Test flatten method."""
        manager = MockOutputManager()

        manager.add("Debug message", LogLevel.DEBUG)
        manager.add("Info message", LogLevel.INFO)
        manager.add("Error message", LogLevel.ERROR)

        # Get all entries flattened
        flattened = manager.flatten(level=LogLevel.DEBUG)
        assert len(flattened) == 3

        # Get only INFO and above
        flattened = manager.flatten(level=LogLevel.INFO)
        assert len(flattened) == 2

    def test_output_sorted(self):
        """Test output_sorted method."""
        manager = MockOutputManager()

        manager.add("Message 1", LogLevel.INFO)
        manager.add("Message 2", LogLevel.ERROR)

        sorted_output = manager.output_sorted()

        assert "Message 1" in sorted_output
        assert "Message 2" in sorted_output

    def test_get_captured_outputs(self):
        """Test get_captured_outputs utility method."""
        manager = MockOutputManager()

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
        manager = MockOutputManager()

        assert manager.get_flush_count() == 0

        manager.flush()
        assert manager.get_flush_count() == 1

        manager.flush()
        assert manager.get_flush_count() == 2

    def test_clear_captured(self):
        """Test clear_captured utility method."""
        manager = MockOutputManager()

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
        manager.add("Debug message", LogLevel.DEBUG)  # Should be filtered out
        manager.add("Info message", LogLevel.INFO)
        manager.add("Warning message", LogLevel.WARNING)
        manager.add("Error message", LogLevel.ERROR)

        # Test output filtering
        output = manager.output(level=LogLevel.INFO)
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
