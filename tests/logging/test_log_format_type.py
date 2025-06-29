"""Tests for LogFormatType enum."""
import pytest
from enum import Enum

from src.logging.log_format_type import LogFormatType


class TestLogFormatType:
    """Test LogFormatType enum."""

    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert hasattr(LogFormatType, 'RAW')
        assert hasattr(LogFormatType, 'PLAIN')
        assert hasattr(LogFormatType, 'CUSTOM')

    def test_enum_inheritance(self):
        """Test that LogFormatType is an Enum."""
        assert issubclass(LogFormatType, Enum)

    def test_enum_unique_values(self):
        """Test that all enum values are unique."""
        values = [member.value for member in LogFormatType]
        assert len(values) == len(set(values))

    def test_enum_member_types(self):
        """Test that all members are LogFormatType instances."""
        for member in LogFormatType:
            assert isinstance(member, LogFormatType)

    def test_enum_string_representation(self):
        """Test string representation of enum members."""
        assert str(LogFormatType.RAW) == "LogFormatType.RAW"
        assert str(LogFormatType.PLAIN) == "LogFormatType.PLAIN"
        assert str(LogFormatType.CUSTOM) == "LogFormatType.CUSTOM"

    def test_enum_name_attribute(self):
        """Test name attribute of enum members."""
        assert LogFormatType.RAW.name == "RAW"
        assert LogFormatType.PLAIN.name == "PLAIN"
        assert LogFormatType.CUSTOM.name == "CUSTOM"

    def test_enum_comparison(self):
        """Test enum member comparison."""
        assert LogFormatType.RAW == LogFormatType.RAW
        assert LogFormatType.RAW != LogFormatType.PLAIN
        assert LogFormatType.RAW != LogFormatType.CUSTOM

    def test_enum_iteration(self):
        """Test iterating over enum members."""
        members = list(LogFormatType)
        assert len(members) == 3
        assert LogFormatType.RAW in members
        assert LogFormatType.PLAIN in members
        assert LogFormatType.CUSTOM in members