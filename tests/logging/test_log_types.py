import pytest
from datetime import datetime
from src.logging.log_types import LogLevel, BaseLogEntry


class TestLogLevel:
    def test_log_level_enum_values(self):
        """Test that LogLevel enum has expected values"""
        # Using auto() means values are integers, not strings
        assert isinstance(LogLevel.DEBUG.value, int)
        assert isinstance(LogLevel.INFO.value, int)
        assert isinstance(LogLevel.WARNING.value, int)
        assert isinstance(LogLevel.ERROR.value, int)
        assert isinstance(LogLevel.CRITICAL.value, int)
    
    def test_log_level_enum_members(self):
        """Test that all expected enum members exist"""
        expected_members = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        actual_members = {member.name for member in LogLevel}
        assert actual_members == expected_members
    
    def test_log_level_comparison(self):
        """Test enum comparison"""
        assert LogLevel.DEBUG == LogLevel.DEBUG
        assert LogLevel.DEBUG != LogLevel.INFO
        assert LogLevel.INFO != LogLevel.WARNING
        assert LogLevel.WARNING != LogLevel.ERROR
        assert LogLevel.ERROR != LogLevel.CRITICAL
    
    def test_log_level_ordering(self):
        """Test that log levels have increasing values"""
        assert LogLevel.DEBUG.value < LogLevel.INFO.value
        assert LogLevel.INFO.value < LogLevel.WARNING.value
        assert LogLevel.WARNING.value < LogLevel.ERROR.value
        assert LogLevel.ERROR.value < LogLevel.CRITICAL.value
    
    def test_log_level_string_representation(self):
        """Test string representation of enum values"""
        assert str(LogLevel.DEBUG) == "LogLevel.DEBUG"
        assert str(LogLevel.INFO) == "LogLevel.INFO"
        assert str(LogLevel.WARNING) == "LogLevel.WARNING"
        assert str(LogLevel.ERROR) == "LogLevel.ERROR"
        assert str(LogLevel.CRITICAL) == "LogLevel.CRITICAL"


class TestBaseLogEntry:
    def test_base_log_entry_creation(self):
        """Test creating a BaseLogEntry"""
        entry = BaseLogEntry(content="Test message", level=LogLevel.INFO)
        assert entry.content == "Test message"
        assert entry.level == LogLevel.INFO
        assert isinstance(entry.timestamp, datetime)
    
    def test_base_log_entry_default_level(self):
        """Test BaseLogEntry with default level"""
        entry = BaseLogEntry(content="Test")
        assert entry.level == LogLevel.INFO
    
    def test_base_log_entry_frozen(self):
        """Test that BaseLogEntry is frozen (immutable)"""
        entry = BaseLogEntry(content="Test", level=LogLevel.DEBUG)
        with pytest.raises(AttributeError):
            entry.content = "Modified"
    
    def test_base_log_entry_custom_timestamp(self):
        """Test BaseLogEntry with custom timestamp"""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        entry = BaseLogEntry(content="Test", timestamp=custom_time)
        assert entry.timestamp == custom_time