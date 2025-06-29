import pytest
from src.application.color_manager import ANSI_CODES, RESET_CODE, to_ansi, apply_color


class TestColorManager:
    """Tests for color management utilities"""
    
    def test_ansi_codes_defined(self):
        """Test that ANSI codes are properly defined"""
        assert len(ANSI_CODES) > 0
        assert "red" in ANSI_CODES
        assert "green" in ANSI_CODES
        assert ANSI_CODES["red"] == "\033[31m"
        assert ANSI_CODES["green"] == "\033[32m"
    
    def test_reset_code_defined(self):
        """Test that reset code is defined"""
        assert RESET_CODE == "\033[0m"
    
    def test_to_ansi_valid_color_name(self):
        """Test converting valid color names to ANSI codes"""
        assert to_ansi("red") == "\033[31m"
        assert to_ansi("green") == "\033[32m"
        assert to_ansi("yellow") == "\033[33m"
        assert to_ansi("blue") == "\033[34m"
        assert to_ansi("magenta") == "\033[35m"
        assert to_ansi("cyan") == "\033[36m"
        assert to_ansi("white") == "\033[37m"
        assert to_ansi("gray") == "\033[90m"
    
    def test_to_ansi_raw_ansi_code(self):
        """Test passing raw ANSI codes through to_ansi"""
        assert to_ansi("\033[31m") == "\033[31m"
        assert to_ansi("\033[1;32m") == "\033[1;32m"
        assert to_ansi("\033[38;5;196m") == "\033[38;5;196m"
    
    def test_to_ansi_invalid_color(self):
        """Test that invalid colors raise ValueError"""
        with pytest.raises(ValueError, match="未対応の色: invalid"):
            to_ansi("invalid")
        
        with pytest.raises(ValueError, match=r"未対応の色: \033\[31"):
            to_ansi("\033[31")  # Missing 'm' at end
        
        with pytest.raises(ValueError, match="未対応の色: 31m"):
            to_ansi("31m")  # Missing escape sequence at start
    
    def test_apply_color_valid(self):
        """Test applying color to text"""
        assert apply_color("Hello", "red") == "\033[31mHello\033[0m"
        assert apply_color("World", "green") == "\033[32mWorld\033[0m"
        assert apply_color("Test", "\033[1;33m") == "\033[1;33mTest\033[0m"
    
    def test_apply_color_empty_text(self):
        """Test applying color to empty text"""
        assert apply_color("", "red") == "\033[31m\033[0m"
    
    def test_apply_color_invalid(self):
        """Test that apply_color raises ValueError for invalid colors"""
        with pytest.raises(ValueError, match="未対応の色: invalid"):
            apply_color("Test", "invalid")