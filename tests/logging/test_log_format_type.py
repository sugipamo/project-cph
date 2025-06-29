"""Tests for LogFormatType enum."""
import pytest
from enum import Enum

from src.logging.log_format_type import LogFormatType


class TestLogFormatType:
    """Test LogFormatType enum."""

    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert hasattr(LogFormatType, 'PLAIN')
        assert hasattr(LogFormatType, 'COLORED')
        assert hasattr(LogFormatType, 'JSON')
        assert hasattr(LogFormatType, 'STRUCTURED')

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
        assert str(LogFormatType.PLAIN) == "LogFormatType.PLAIN"
        assert str(LogFormatType.COLORED) == "LogFormatType.COLORED"
        assert str(LogFormatType.JSON) == "LogFormatType.JSON"
        assert str(LogFormatType.STRUCTURED) == "LogFormatType.STRUCTURED"

    def test_enum_name_attribute(self):
        """Test name attribute of enum members."""
        assert LogFormatType.PLAIN.name == "PLAIN"
        assert LogFormatType.COLORED.name == "COLORED"
        assert LogFormatType.JSON.name == "JSON"
        assert LogFormatType.STRUCTURED.name == "STRUCTURED"

    def test_enum_comparison(self):
        """Test enum member comparison."""
        assert LogFormatType.PLAIN == LogFormatType.PLAIN
        assert LogFormatType.PLAIN != LogFormatType.COLORED
        assert LogFormatType.COLORED != LogFormatType.JSON
        assert LogFormatType.JSON != LogFormatType.STRUCTURED

    def test_enum_iteration(self):
        """Test iterating over enum members."""
        members = list(LogFormatType)
        assert len(members) == 4
        assert LogFormatType.PLAIN in members
        assert LogFormatType.COLORED in members
        assert LogFormatType.JSON in members
        assert LogFormatType.STRUCTURED in members