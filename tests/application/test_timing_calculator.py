"""Tests for timing_calculator.py - pure functions for execution time calculation"""
import pytest
from unittest.mock import Mock
from src.application.timing_calculator import (
    ExecutionTiming,
    start_timing,
    end_timing,
    format_execution_timing,
    is_execution_timeout
)


class TestExecutionTiming:
    """Test ExecutionTiming dataclass"""
    
    def test_creation_with_start_time_only(self):
        """Test creating ExecutionTiming with only start time"""
        timing = ExecutionTiming(start_time=100.0)
        assert timing.start_time == 100.0
        assert timing.end_time is None
        assert timing.duration is None
    
    def test_creation_with_both_times(self):
        """Test creating ExecutionTiming with start and end times"""
        timing = ExecutionTiming(start_time=100.0, end_time=105.5)
        assert timing.start_time == 100.0
        assert timing.end_time == 105.5
        assert timing.duration == 5.5
    
    def test_duration_calculation(self):
        """Test duration property calculation"""
        timing = ExecutionTiming(start_time=100.0, end_time=110.0)
        assert timing.duration == 10.0
        
        timing_no_end = ExecutionTiming(start_time=100.0)
        assert timing_no_end.duration is None
    
    def test_with_end_time(self):
        """Test creating new instance with end time"""
        timing = ExecutionTiming(start_time=100.0)
        new_timing = timing.with_end_time(150.0)
        
        # Original should be unchanged (immutable)
        assert timing.end_time is None
        assert timing.duration is None
        
        # New instance should have end time
        assert new_timing.start_time == 100.0
        assert new_timing.end_time == 150.0
        assert new_timing.duration == 50.0
    
    def test_immutability(self):
        """Test that ExecutionTiming is immutable"""
        timing = ExecutionTiming(start_time=100.0)
        with pytest.raises(AttributeError):
            timing.start_time = 200.0
        with pytest.raises(AttributeError):
            timing.end_time = 150.0


class TestTimingFunctions:
    """Test timing calculator functions"""
    
    def test_start_timing(self):
        """Test start_timing function"""
        mock_time_provider = Mock()
        mock_time_provider.now.return_value = 123.456
        
        timing = start_timing(mock_time_provider)
        
        mock_time_provider.now.assert_called_once()
        assert timing.start_time == 123.456
        assert timing.end_time is None
    
    def test_end_timing(self):
        """Test end_timing function"""
        mock_time_provider = Mock()
        mock_time_provider.now.return_value = 150.0
        
        initial_timing = ExecutionTiming(start_time=100.0)
        final_timing = end_timing(initial_timing, mock_time_provider)
        
        mock_time_provider.now.assert_called_once()
        assert final_timing.start_time == 100.0
        assert final_timing.end_time == 150.0
        assert final_timing.duration == 50.0
    
    def test_format_execution_timing_no_end_time(self):
        """Test formatting when execution is still running"""
        timing = ExecutionTiming(start_time=100.0)
        result = format_execution_timing(timing)
        assert result == "実行中..."
    
    def test_format_execution_timing_milliseconds(self):
        """Test formatting for durations less than 1 second"""
        timing = ExecutionTiming(start_time=100.0, end_time=100.123)
        result = format_execution_timing(timing)
        assert result == "123.0ms"
        
        timing2 = ExecutionTiming(start_time=100.0, end_time=100.999)
        result2 = format_execution_timing(timing2)
        assert result2 == "999.0ms"
    
    def test_format_execution_timing_seconds(self):
        """Test formatting for durations between 1 and 60 seconds"""
        timing = ExecutionTiming(start_time=100.0, end_time=101.0)
        result = format_execution_timing(timing)
        assert result == "1.00s"
        
        timing2 = ExecutionTiming(start_time=100.0, end_time=159.99)
        result2 = format_execution_timing(timing2)
        assert result2 == "59.99s"
    
    def test_format_execution_timing_minutes(self):
        """Test formatting for durations over 60 seconds"""
        timing = ExecutionTiming(start_time=100.0, end_time=160.0)
        result = format_execution_timing(timing)
        assert result == "1m 0.0s"
        
        timing2 = ExecutionTiming(start_time=100.0, end_time=223.5)
        result2 = format_execution_timing(timing2)
        assert result2 == "2m 3.5s"
    
    def test_is_execution_timeout_no_duration(self):
        """Test timeout check when no duration is available"""
        timing = ExecutionTiming(start_time=100.0)
        result = is_execution_timeout(timing, 10.0)
        assert result is False
    
    def test_is_execution_timeout_within_limit(self):
        """Test timeout check when execution is within limit"""
        timing = ExecutionTiming(start_time=100.0, end_time=105.0)
        result = is_execution_timeout(timing, 10.0)
        assert result is False
    
    def test_is_execution_timeout_exceeded(self):
        """Test timeout check when execution exceeds limit"""
        timing = ExecutionTiming(start_time=100.0, end_time=115.0)
        result = is_execution_timeout(timing, 10.0)
        assert result is True
        
        # Test exact boundary
        timing2 = ExecutionTiming(start_time=100.0, end_time=110.0)
        result2 = is_execution_timeout(timing2, 10.0)
        assert result2 is False
        
        timing3 = ExecutionTiming(start_time=100.0, end_time=110.001)
        result3 = is_execution_timeout(timing3, 10.0)
        assert result3 is True


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_zero_duration(self):
        """Test handling of zero duration"""
        timing = ExecutionTiming(start_time=100.0, end_time=100.0)
        assert timing.duration == 0.0
        assert format_execution_timing(timing) == "0.0ms"
        assert is_execution_timeout(timing, 0.001) is False
    
    def test_negative_duration(self):
        """Test handling of negative duration (edge case)"""
        # This shouldn't happen in practice, but let's test it
        timing = ExecutionTiming(start_time=100.0, end_time=90.0)
        assert timing.duration == -10.0
        # The formatter should still work
        assert format_execution_timing(timing) == "-10000.0ms"
    
    def test_very_long_duration(self):
        """Test formatting of very long durations"""
        # 1 hour 30 minutes 45.5 seconds
        timing = ExecutionTiming(start_time=0.0, end_time=5445.5)
        result = format_execution_timing(timing)
        assert result == "90m 45.5s"