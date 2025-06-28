"""Tests for log_types module."""
from datetime import datetime
import pytest

from src.utils.log_types import LogLevel, BaseLogEntry


class TestLogLevel:
    """Test cases for LogLevel enum."""

    def test_log_level_values(self):
        """Test that all log levels are defined."""
        assert LogLevel.DEBUG is not None
        assert LogLevel.INFO is not None
        assert LogLevel.WARNING is not None
        assert LogLevel.ERROR is not None
        assert LogLevel.CRITICAL is not None

    def test_log_level_ordering(self):
        """Test log level ordering (by enum value)."""
        # Enum auto() assigns incrementing values
        assert LogLevel.DEBUG.value < LogLevel.INFO.value
        assert LogLevel.INFO.value < LogLevel.WARNING.value
        assert LogLevel.WARNING.value < LogLevel.ERROR.value
        assert LogLevel.ERROR.value < LogLevel.CRITICAL.value

    def test_log_level_names(self):
        """Test log level string names."""
        assert LogLevel.DEBUG.name == "DEBUG"
        assert LogLevel.INFO.name == "INFO"
        assert LogLevel.WARNING.name == "WARNING"
        assert LogLevel.ERROR.name == "ERROR"
        assert LogLevel.CRITICAL.name == "CRITICAL"

    def test_log_level_uniqueness(self):
        """Test that all log levels are unique."""
        levels = list(LogLevel)
        assert len(levels) == 5
        assert len(set(levels)) == 5


class TestBaseLogEntry:
    """Test cases for BaseLogEntry dataclass."""

    def test_init_defaults(self):
        """Test BaseLogEntry initialization with defaults."""
        entry = BaseLogEntry(content="Test message")
        
        assert entry.content == "Test message"
        assert entry.level == LogLevel.INFO
        assert isinstance(entry.timestamp, datetime)

    def test_init_with_all_fields(self):
        """Test BaseLogEntry initialization with all fields."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        entry = BaseLogEntry(
            content="Error occurred",
            level=LogLevel.ERROR,
            timestamp=timestamp
        )
        
        assert entry.content == "Error occurred"
        assert entry.level == LogLevel.ERROR
        assert entry.timestamp == timestamp

    def test_timestamp_default_factory(self):
        """Test that timestamp uses current time by default."""
        before = datetime.now()
        entry = BaseLogEntry(content="Test")
        after = datetime.now()
        
        assert before <= entry.timestamp <= after

    def test_frozen_dataclass(self):
        """Test that BaseLogEntry is frozen (immutable)."""
        entry = BaseLogEntry(content="Test")
        
        with pytest.raises(AttributeError):
            entry.content = "Modified"
        
        with pytest.raises(AttributeError):
            entry.level = LogLevel.ERROR

    def test_different_log_levels(self):
        """Test creating entries with different log levels."""
        debug_entry = BaseLogEntry(content="Debug", level=LogLevel.DEBUG)
        info_entry = BaseLogEntry(content="Info", level=LogLevel.INFO)
        warning_entry = BaseLogEntry(content="Warning", level=LogLevel.WARNING)
        error_entry = BaseLogEntry(content="Error", level=LogLevel.ERROR)
        critical_entry = BaseLogEntry(content="Critical", level=LogLevel.CRITICAL)
        
        assert debug_entry.level == LogLevel.DEBUG
        assert info_entry.level == LogLevel.INFO
        assert warning_entry.level == LogLevel.WARNING
        assert error_entry.level == LogLevel.ERROR
        assert critical_entry.level == LogLevel.CRITICAL

    def test_equality(self):
        """Test BaseLogEntry equality."""
        timestamp = datetime.now()
        entry1 = BaseLogEntry(
            content="Test",
            level=LogLevel.INFO,
            timestamp=timestamp
        )
        entry2 = BaseLogEntry(
            content="Test",
            level=LogLevel.INFO,
            timestamp=timestamp
        )
        entry3 = BaseLogEntry(
            content="Different",
            level=LogLevel.INFO,
            timestamp=timestamp
        )
        
        assert entry1 == entry2
        assert entry1 != entry3

    def test_hash(self):
        """Test that BaseLogEntry is hashable (due to frozen=True)."""
        timestamp = datetime.now()
        entry = BaseLogEntry(
            content="Test",
            level=LogLevel.INFO,
            timestamp=timestamp
        )
        
        # Should be able to use as dict key or in set
        entry_set = {entry}
        assert entry in entry_set
        
        entry_dict = {entry: "value"}
        assert entry_dict[entry] == "value"