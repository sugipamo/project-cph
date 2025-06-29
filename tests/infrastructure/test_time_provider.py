"""Tests for time provider implementations."""
import pytest
import time
from unittest.mock import patch
from src.infrastructure.time_provider import (
    SystemTimeProvider,
    MockTimeProvider,
    FixedTimeProvider,
    calculate_duration,
    format_duration,
    is_timeout_exceeded
)


class TestSystemTimeProvider:
    """Test cases for SystemTimeProvider."""

    @patch('time.time')
    def test_now_returns_current_time(self, mock_time):
        """Test now returns current time from time.time()."""
        mock_time.return_value = 1234567890.123
        provider = SystemTimeProvider()
        
        result = provider.now()
        
        assert result == 1234567890.123
        mock_time.assert_called_once()

    @patch('time.sleep')
    def test_sleep_delegates_to_time_sleep(self, mock_sleep):
        """Test sleep delegates to time.sleep()."""
        provider = SystemTimeProvider()
        
        provider.sleep(2.5)
        
        mock_sleep.assert_called_once_with(2.5)


class TestMockTimeProvider:
    """Test cases for MockTimeProvider."""

    def test_init_with_default_time(self):
        """Test initialization with default time."""
        provider = MockTimeProvider()
        assert provider._current_time == 0.0
        assert provider._sleep_calls == []

    def test_init_with_custom_time(self):
        """Test initialization with custom initial time."""
        provider = MockTimeProvider(initial_time=1000.0)
        assert provider._current_time == 1000.0

    def test_now_returns_current_time(self):
        """Test now returns current mock time."""
        provider = MockTimeProvider(initial_time=500.0)
        assert provider.now() == 500.0

    def test_sleep_records_call_and_advances_time(self):
        """Test sleep records call and advances time."""
        provider = MockTimeProvider(initial_time=100.0)
        
        provider.sleep(5.0)
        
        assert provider.now() == 105.0
        assert provider.get_sleep_calls() == [5.0]

    def test_multiple_sleep_calls(self):
        """Test multiple sleep calls accumulate."""
        provider = MockTimeProvider()
        
        provider.sleep(1.0)
        provider.sleep(2.5)
        provider.sleep(0.5)
        
        assert provider.now() == 4.0
        assert provider.get_sleep_calls() == [1.0, 2.5, 0.5]

    def test_advance_time(self):
        """Test advance_time moves time forward."""
        provider = MockTimeProvider(initial_time=100.0)
        
        provider.advance_time(50.0)
        
        assert provider.now() == 150.0

    def test_set_time(self):
        """Test set_time sets absolute time."""
        provider = MockTimeProvider(initial_time=100.0)
        
        provider.set_time(2000.0)
        
        assert provider.now() == 2000.0

    def test_get_sleep_calls_returns_copy(self):
        """Test get_sleep_calls returns a copy."""
        provider = MockTimeProvider()
        provider.sleep(1.0)
        
        calls = provider.get_sleep_calls()
        calls.append(999.0)
        
        assert provider.get_sleep_calls() == [1.0]


class TestFixedTimeProvider:
    """Test cases for FixedTimeProvider."""

    def test_init_with_fixed_time(self):
        """Test initialization with fixed time."""
        provider = FixedTimeProvider(fixed_time=1234.5)
        assert provider._fixed_time == 1234.5

    def test_now_always_returns_fixed_time(self):
        """Test now always returns the same fixed time."""
        provider = FixedTimeProvider(fixed_time=9999.0)
        
        assert provider.now() == 9999.0
        assert provider.now() == 9999.0
        assert provider.now() == 9999.0

    def test_sleep_does_nothing(self):
        """Test sleep does nothing for fixed time provider."""
        provider = FixedTimeProvider(fixed_time=1000.0)
        
        provider.sleep(100.0)
        
        # Time should not change
        assert provider.now() == 1000.0


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_calculate_duration(self):
        """Test calculate_duration calculates elapsed time."""
        assert calculate_duration(100.0, 150.5) == 50.5
        assert calculate_duration(0.0, 10.0) == 10.0
        assert calculate_duration(1000.0, 1000.0) == 0.0
        assert calculate_duration(100.0, 90.0) == -10.0  # Negative duration

    def test_format_duration_milliseconds(self):
        """Test format_duration for sub-second durations."""
        assert format_duration(0.001) == "1.0ms"
        assert format_duration(0.1234) == "123.4ms"
        assert format_duration(0.999) == "999.0ms"

    def test_format_duration_seconds(self):
        """Test format_duration for seconds."""
        assert format_duration(1.0) == "1.00s"
        assert format_duration(10.5) == "10.50s"
        assert format_duration(59.99) == "59.99s"

    def test_format_duration_minutes(self):
        """Test format_duration for minutes and seconds."""
        assert format_duration(60.0) == "1m 0.0s"
        assert format_duration(65.5) == "1m 5.5s"
        assert format_duration(125.7) == "2m 5.7s"
        assert format_duration(3661.2) == "61m 1.2s"

    def test_is_timeout_exceeded(self):
        """Test is_timeout_exceeded checks timeout condition."""
        # Not exceeded
        assert is_timeout_exceeded(100.0, 105.0, 10.0) is False
        assert is_timeout_exceeded(100.0, 110.0, 10.0) is False
        
        # Exceeded
        assert is_timeout_exceeded(100.0, 111.0, 10.0) is True
        assert is_timeout_exceeded(100.0, 200.0, 10.0) is True
        
        # Edge case - exactly at timeout
        assert is_timeout_exceeded(100.0, 110.0, 10.0) is False