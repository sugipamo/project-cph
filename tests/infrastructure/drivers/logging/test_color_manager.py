"""Tests for color manager"""
import pytest

from src.infrastructure.drivers.logging.color_manager import (
    ANSI_CODES,
    RESET_CODE,
    apply_color,
    to_ansi,
)


class TestColorManager:
    """Test color management functions"""

    def test_ansi_codes_constants(self):
        """Test ANSI color codes are properly defined"""
        expected_colors = {
            "red", "green", "yellow", "blue", "magenta", "cyan", "white", "gray"
        }
        assert set(ANSI_CODES.keys()) == expected_colors
        assert all(code.startswith("\033[") and code.endswith("m") for code in ANSI_CODES.values())

    def test_reset_code_constant(self):
        """Test RESET_CODE is properly defined"""
        assert RESET_CODE == "\033[0m"

    def test_to_ansi_valid_color_names(self):
        """Test to_ansi with valid color names"""
        assert to_ansi("red") == "\033[31m"
        assert to_ansi("green") == "\033[32m"
        assert to_ansi("yellow") == "\033[33m"
        assert to_ansi("blue") == "\033[34m"
        assert to_ansi("magenta") == "\033[35m"
        assert to_ansi("cyan") == "\033[36m"
        assert to_ansi("white") == "\033[37m"
        assert to_ansi("gray") == "\033[90m"

    def test_to_ansi_valid_ansi_code(self):
        """Test to_ansi with valid ANSI codes"""
        assert to_ansi("\033[31m") == "\033[31m"
        assert to_ansi("\033[32m") == "\033[32m"
        assert to_ansi("\033[1;31m") == "\033[1;31m"

    def test_to_ansi_invalid_color_name(self):
        """Test to_ansi with invalid color name"""
        with pytest.raises(ValueError, match="未対応の色: invalid"):
            to_ansi("invalid")

    def test_to_ansi_invalid_ansi_code_missing_prefix(self):
        """Test to_ansi with invalid ANSI code missing prefix"""
        with pytest.raises(ValueError, match="未対応の色: 31m"):
            to_ansi("31m")

    def test_to_ansi_invalid_ansi_code_missing_suffix(self):
        """Test to_ansi with invalid ANSI code missing suffix"""
        with pytest.raises(ValueError, match="未対応の色: \\033\\[31"):
            to_ansi("\033[31")

    def test_to_ansi_empty_string(self):
        """Test to_ansi with empty string"""
        with pytest.raises(ValueError, match="未対応の色: "):
            to_ansi("")

    def test_apply_color_with_color_name(self):
        """Test apply_color with color name"""
        result = apply_color("test", "red")
        assert result == "\033[31mtest\033[0m"

    def test_apply_color_with_ansi_code(self):
        """Test apply_color with ANSI code"""
        result = apply_color("test", "\033[32m")
        assert result == "\033[32mtest\033[0m"

    def test_apply_color_with_empty_text(self):
        """Test apply_color with empty text"""
        result = apply_color("", "red")
        assert result == "\033[31m\033[0m"

    def test_apply_color_with_multiline_text(self):
        """Test apply_color with multiline text"""
        text = "line1\nline2"
        result = apply_color(text, "blue")
        assert result == "\033[34mline1\nline2\033[0m"

    def test_apply_color_with_invalid_color(self):
        """Test apply_color with invalid color"""
        with pytest.raises(ValueError, match="未対応の色: invalid"):
            apply_color("test", "invalid")

    def test_apply_color_preserves_text_content(self):
        """Test apply_color preserves the original text content"""
        original_text = "Hello, World! 123 @#$%"
        result = apply_color(original_text, "green")
        # Remove color codes to check if original text is preserved
        text_without_colors = result.replace("\033[32m", "").replace("\033[0m", "")
        assert text_without_colors == original_text

    def test_all_color_names_work_with_apply_color(self):
        """Test that all defined color names work with apply_color"""
        test_text = "test"
        for color_name in ANSI_CODES:
            result = apply_color(test_text, color_name)
            expected_prefix = ANSI_CODES[color_name]
            expected_suffix = RESET_CODE
            assert result.startswith(expected_prefix)
            assert result.endswith(expected_suffix)
            assert test_text in result
