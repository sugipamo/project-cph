"""Tests for FormatInfo class."""
import pytest

from src.utils.format_info import FormatInfo
from src.logging.log_format_type import LogFormatType


class TestFormatInfo:
    """Test FormatInfo class."""

    def test_init_default(self):
        """Test initialization with default values."""
        info = FormatInfo()
        
        assert info.formattype == LogFormatType.PLAIN
        assert info.color is None
        assert info.bold is False
        assert info.indent == 0

    def test_init_with_values(self):
        """Test initialization with specific values."""
        info = FormatInfo(
            formattype=LogFormatType.COLORED,
            color="red",
            bold=True,
            indent=2
        )
        
        assert info.formattype == LogFormatType.COLORED
        assert info.color == "red"
        assert info.bold is True
        assert info.indent == 2

    def test_post_init_sets_default_formattype(self):
        """Test that __post_init__ sets default formattype."""
        info = FormatInfo(color="blue", bold=True)
        
        assert info.formattype == LogFormatType.PLAIN

    def test_to_dict(self):
        """Test conversion to dictionary."""
        info = FormatInfo(
            formattype=LogFormatType.COLORED,
            color="green",
            bold=True,
            indent=1
        )
        
        result = info.to_dict()
        
        assert result == {
            'formattype': 'COLORED',
            'color': 'green',
            'bold': True
        }
        # Note: indent is not included in to_dict()

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'formattype': 'PLAIN',
            'color': 'yellow',
            'bold': False
        }
        
        info = FormatInfo.from_dict(data)
        
        assert info.formattype == LogFormatType.PLAIN
        assert info.color == "yellow"
        assert info.bold is False
        assert info.indent == 0  # Default value

    def test_apply_plain_format(self):
        """Test apply with PLAIN format type."""
        info = FormatInfo(formattype=LogFormatType.PLAIN)
        
        # PLAIN format removes ANSI codes
        text_with_ansi = "\x1b[31mRed text\x1b[0m"
        result = info.apply(text_with_ansi)
        
        assert result == "Red text"

    def test_apply_structured_format(self):
        """Test apply with STRUCTURED format type."""
        info = FormatInfo(formattype=LogFormatType.STRUCTURED)
        
        # STRUCTURED format preserves text as-is
        text = "Test text"
        result = info.apply(text)
        
        assert result == text

    def test_apply_custom_format_with_color(self):
        """Test apply with CUSTOM format and color."""
        info = FormatInfo(
            formattype=LogFormatType.COLORED,
            color="blue"
        )
        
        result = info.apply("Test text")
        
        # Should apply blue color
        assert "\x1b[" in result
        assert "Test text" in result
        assert result.endswith("\x1b[0m")

    def test_apply_custom_format_with_bold(self):
        """Test apply with CUSTOM format and bold."""
        info = FormatInfo(
            formattype=LogFormatType.COLORED,
            bold=True
        )
        
        result = info.apply("Test text")
        
        # Should apply bold
        assert result == "\x1b[1mTest text\x1b[0m"

    def test_apply_custom_format_with_color_and_bold(self):
        """Test apply with CUSTOM format, color, and bold."""
        info = FormatInfo(
            formattype=LogFormatType.COLORED,
            color="red",
            bold=True
        )
        
        result = info.apply("Test text")
        
        # Should have both color and bold codes
        assert "\x1b[" in result
        assert "\x1b[1m" in result
        assert "Test text" in result

    def test_apply_with_indent(self):
        """Test apply with indentation."""
        info = FormatInfo(
            formattype=LogFormatType.PLAIN,
            indent=2
        )
        
        result = info.apply("Test text")
        
        assert result == "        Test text"  # 8 spaces (2 * 4)

    def test_apply_with_indent_and_formatting(self):
        """Test apply with indent and other formatting."""
        info = FormatInfo(
            formattype=LogFormatType.COLORED,
            color="green",
            bold=True,
            indent=1
        )
        
        result = info.apply("Test text")
        
        # The color and bold formatting wrap the indented text
        assert "    Test text" in result
        assert "\x1b[" in result
        assert "\x1b[1m" in result  # Bold
        assert "\x1b[32m" in result  # Green color

    def test_remove_ansi_various_codes(self):
        """Test ANSI removal with various escape codes."""
        info = FormatInfo(formattype=LogFormatType.PLAIN)
        
        test_cases = [
            ("\x1b[0mNormal\x1b[0m", "Normal"),
            ("\x1b[1mBold\x1b[0m", "Bold"),
            ("\x1b[31mRed\x1b[0m", "Red"),
            ("\x1b[1;31mBold Red\x1b[0m", "Bold Red"),
            ("\x1b[38;5;123mExtended Color\x1b[0m", "Extended Color"),
            ("\x1b[48;2;255;0;0mRGB Background\x1b[0m", "RGB Background"),
            ("\x1b[2J\x1b[H", ""),  # Clear screen and home
            ("No ANSI here", "No ANSI here"),
        ]
        
        for input_text, expected in test_cases:
            result = info.apply(input_text)
            assert result == expected