"""Tests for time provider implementations."""
import time

import pytest

from src.infrastructure.providers.time_provider import (
    FixedTimeProvider,
    MockTimeProvider,
    SystemTimeProvider,
    calculate_duration,
    format_duration,
    is_timeout_exceeded,
)


class TestSystemTimeProvider:
    """Test SystemTimeProvider functionality."""

    @pytest.fixture
    def time_provider(self):
        """Create SystemTimeProvider instance."""
        return SystemTimeProvider()

    def test_now_returns_float(self, time_provider):
        """Test now() returns a float timestamp."""
        result = time_provider.now()
        assert isinstance(result, float)

    def test_now_returns_current_time(self, time_provider):
        """Test now() returns current system time."""
        before = time.time()
        result = time_provider.now()
        after = time.time()

        # Should be between before and after
        assert before <= result <= after

    def test_sleep_duration(self, time_provider):
        """Test sleep() waits for specified duration."""
        start = time.time()
        time_provider.sleep(0.1)  # Sleep for 100ms
        end = time.time()

        duration = end - start
        # Should be approximately 0.1 seconds (with some tolerance)
        assert 0.08 <= duration <= 0.15


class TestMockTimeProvider:
    """Test MockTimeProvider functionality."""

    def test_initial_time_default(self):
        """Test MockTimeProvider with default initial time."""
        provider = MockTimeProvider()
        assert provider.now() == 0.0

    def test_initial_time_custom(self):
        """Test MockTimeProvider with custom initial time."""
        provider = MockTimeProvider(initial_time=1234.5)
        assert provider.now() == 1234.5

    def test_advance_time(self):
        """Test advancing time manually."""
        provider = MockTimeProvider(initial_time=100.0)

        provider.advance_time(50.0)
        assert provider.now() == 150.0

        provider.advance_time(25.5)
        assert provider.now() == 175.5

    def test_set_time(self):
        """Test setting time directly."""
        provider = MockTimeProvider(initial_time=100.0)

        provider.set_time(500.0)
        assert provider.now() == 500.0

        provider.set_time(0.0)
        assert provider.now() == 0.0

    def test_sleep_advances_time(self):
        """Test sleep() advances mock time."""
        provider = MockTimeProvider(initial_time=100.0)

        provider.sleep(30.0)
        assert provider.now() == 130.0

        provider.sleep(20.5)
        assert provider.now() == 150.5

    def test_sleep_call_tracking(self):
        """Test sleep() calls are tracked."""
        provider = MockTimeProvider()

        provider.sleep(10.0)
        provider.sleep(5.5)
        provider.sleep(2.0)

        sleep_calls = provider.get_sleep_calls()
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == 10.0
        assert sleep_calls[1] == 5.5
        assert sleep_calls[2] == 2.0

    def test_get_sleep_calls_returns_copy(self):
        """Test get_sleep_calls returns independent copy."""
        provider = MockTimeProvider()
        provider.sleep(1.0)

        calls1 = provider.get_sleep_calls()
        calls2 = provider.get_sleep_calls()

        # Should be equal but not the same object
        assert calls1 == calls2
        assert calls1 is not calls2

        # Modifying one shouldn't affect the other
        calls1.append(2.0)
        assert len(calls2) == 1
        assert len(provider.get_sleep_calls()) == 1

    def test_negative_time_operations(self):
        """Test behavior with negative time values."""
        provider = MockTimeProvider(initial_time=100.0)

        # Negative advance should decrease time
        provider.advance_time(-50.0)
        assert provider.now() == 50.0

        # Negative sleep should still be tracked
        provider.sleep(-10.0)
        assert provider.now() == 40.0

        sleep_calls = provider.get_sleep_calls()
        assert sleep_calls[-1] == -10.0


class TestFixedTimeProvider:
    """Test FixedTimeProvider functionality."""

    def test_fixed_time_returned(self):
        """Test fixed time is always returned."""
        provider = FixedTimeProvider(fixed_time=12345.67)

        # Should always return the same time
        assert provider.now() == 12345.67
        assert provider.now() == 12345.67
        assert provider.now() == 12345.67

    def test_sleep_does_nothing(self):
        """Test sleep() does nothing in fixed time provider."""
        provider = FixedTimeProvider(fixed_time=100.0)

        provider.sleep(50.0)
        assert provider.now() == 100.0  # Should not change

        provider.sleep(1000.0)
        assert provider.now() == 100.0  # Should still not change

    def test_zero_time(self):
        """Test FixedTimeProvider with zero time."""
        provider = FixedTimeProvider(fixed_time=0.0)
        assert provider.now() == 0.0

    def test_negative_time(self):
        """Test FixedTimeProvider with negative time."""
        provider = FixedTimeProvider(fixed_time=-123.45)
        assert provider.now() == -123.45


class TestTimeUtilityFunctions:
    """Test utility functions for time operations."""

    def test_calculate_duration_positive(self):
        """Test calculate_duration with positive duration."""
        start = 100.0
        end = 150.5
        duration = calculate_duration(start, end)
        assert duration == 50.5

    def test_calculate_duration_zero(self):
        """Test calculate_duration with zero duration."""
        start = 100.0
        end = 100.0
        duration = calculate_duration(start, end)
        assert duration == 0.0

    def test_calculate_duration_negative(self):
        """Test calculate_duration with negative duration."""
        start = 150.0
        end = 100.0
        duration = calculate_duration(start, end)
        assert duration == -50.0

    def test_format_duration_milliseconds(self):
        """Test format_duration for sub-second durations."""
        assert format_duration(0.5) == "500.0ms"
        assert format_duration(0.123) == "123.0ms"
        assert format_duration(0.001) == "1.0ms"
        assert format_duration(0.9999) == "999.9ms"

    def test_format_duration_seconds(self):
        """Test format_duration for second durations."""
        assert format_duration(1.0) == "1.00s"
        assert format_duration(30.5) == "30.50s"
        assert format_duration(59.99) == "59.99s"

    def test_format_duration_minutes(self):
        """Test format_duration for minute durations."""
        assert format_duration(60.0) == "1m 0.0s"
        assert format_duration(90.5) == "1m 30.5s"
        assert format_duration(125.3) == "2m 5.3s"
        assert format_duration(3661.0) == "61m 1.0s"

    def test_format_duration_edge_cases(self):
        """Test format_duration edge cases."""
        assert format_duration(0.0) == "0.0ms"
        assert format_duration(59.9999) == "60.00s"  # Rounds to 60.00s
        assert format_duration(60.0001) == "1m 0.0s"   # Just over 1 minute

    def test_is_timeout_exceeded_not_exceeded(self):
        """Test is_timeout_exceeded when timeout not exceeded."""
        start_time = 100.0
        current_time = 130.0
        timeout_seconds = 40.0

        result = is_timeout_exceeded(start_time, current_time, timeout_seconds)
        assert result is False

    def test_is_timeout_exceeded_exactly_at_timeout(self):
        """Test is_timeout_exceeded when exactly at timeout."""
        start_time = 100.0
        current_time = 140.0
        timeout_seconds = 40.0

        result = is_timeout_exceeded(start_time, current_time, timeout_seconds)
        assert result is False  # Should not be exceeded when exactly equal

    def test_is_timeout_exceeded_exceeded(self):
        """Test is_timeout_exceeded when timeout exceeded."""
        start_time = 100.0
        current_time = 141.0
        timeout_seconds = 40.0

        result = is_timeout_exceeded(start_time, current_time, timeout_seconds)
        assert result is True

    def test_is_timeout_exceeded_zero_timeout(self):
        """Test is_timeout_exceeded with zero timeout."""
        start_time = 100.0
        current_time = 100.1
        timeout_seconds = 0.0

        result = is_timeout_exceeded(start_time, current_time, timeout_seconds)
        assert result is True

    def test_is_timeout_exceeded_negative_values(self):
        """Test is_timeout_exceeded with negative values."""
        start_time = -50.0
        current_time = -20.0
        timeout_seconds = 20.0

        result = is_timeout_exceeded(start_time, current_time, timeout_seconds)
        assert result is True  # 30 seconds elapsed, timeout is 20

    def test_is_timeout_exceeded_current_before_start(self):
        """Test is_timeout_exceeded when current time is before start time."""
        start_time = 100.0
        current_time = 90.0
        timeout_seconds = 20.0

        result = is_timeout_exceeded(start_time, current_time, timeout_seconds)
        assert result is False  # Negative duration should not be considered timeout
