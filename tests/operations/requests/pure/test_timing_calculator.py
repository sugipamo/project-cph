"""Tests for timing calculator pure functions."""
from unittest.mock import Mock

import pytest

from src.infrastructure.providers.time_provider import TimeProvider
from src.infrastructure.requests.pure.timing_calculator import (
    ExecutionTiming,
    end_timing,
    format_execution_timing,
    is_execution_timeout,
    start_timing,
)


class TestExecutionTiming:
    """Test ExecutionTiming dataclass."""

    def test_init_with_start_time_only(self):
        timing = ExecutionTiming(start_time=100.0)
        assert timing.start_time == 100.0
        assert timing.end_time is None
        assert timing.duration is None

    def test_init_with_both_times(self):
        timing = ExecutionTiming(start_time=100.0, end_time=110.5)
        assert timing.start_time == 100.0
        assert timing.end_time == 110.5
        assert timing.duration == 10.5

    def test_with_end_time_creates_new_instance(self):
        timing1 = ExecutionTiming(start_time=100.0)
        timing2 = timing1.with_end_time(120.0)

        # 元のインスタンスは変更されない
        assert timing1.end_time is None
        assert timing1.duration is None

        # 新しいインスタンスには終了時刻が設定される
        assert timing2.start_time == 100.0
        assert timing2.end_time == 120.0
        assert timing2.duration == 20.0



class TestTimingFunctions:
    """Test timing calculator functions."""

    def test_start_timing(self):
        mock_time_provider = Mock(spec=TimeProvider)
        mock_time_provider.now.return_value = 150.5

        timing = start_timing(mock_time_provider)

        assert timing.start_time == 150.5
        assert timing.end_time is None
        mock_time_provider.now.assert_called_once()

    def test_end_timing(self):
        mock_time_provider = Mock(spec=TimeProvider)
        mock_time_provider.now.return_value = 200.5

        initial_timing = ExecutionTiming(start_time=100.0)
        final_timing = end_timing(initial_timing, mock_time_provider)

        assert final_timing.start_time == 100.0
        assert final_timing.end_time == 200.5
        assert final_timing.duration == 100.5
        mock_time_provider.now.assert_called_once()

    def test_format_execution_timing_running(self):
        timing = ExecutionTiming(start_time=100.0)
        formatted = format_execution_timing(timing)
        assert formatted == "実行中..."

    def test_format_execution_timing_milliseconds(self):
        # 0.5秒 = 500ms
        timing = ExecutionTiming(start_time=100.0, end_time=100.5)
        formatted = format_execution_timing(timing)
        assert formatted == "500.0ms"

        # 0.123秒 = 123ms
        timing = ExecutionTiming(start_time=100.0, end_time=100.123)
        formatted = format_execution_timing(timing)
        assert formatted == "123.0ms"

    def test_format_execution_timing_seconds(self):
        # 1.5秒
        timing = ExecutionTiming(start_time=100.0, end_time=101.5)
        formatted = format_execution_timing(timing)
        assert formatted == "1.50s"

        # 59.99秒
        timing = ExecutionTiming(start_time=100.0, end_time=159.99)
        formatted = format_execution_timing(timing)
        assert formatted == "59.99s"

    def test_format_execution_timing_minutes(self):
        # 60秒 = 1分0秒
        timing = ExecutionTiming(start_time=100.0, end_time=160.0)
        formatted = format_execution_timing(timing)
        assert formatted == "1m 0.0s"

        # 125.5秒 = 2分5.5秒
        timing = ExecutionTiming(start_time=100.0, end_time=225.5)
        formatted = format_execution_timing(timing)
        assert formatted == "2m 5.5s"

    def test_is_execution_timeout_no_duration(self):
        timing = ExecutionTiming(start_time=100.0)
        assert not is_execution_timeout(timing, 10.0)

    def test_is_execution_timeout_within_limit(self):
        timing = ExecutionTiming(start_time=100.0, end_time=105.0)
        assert not is_execution_timeout(timing, 10.0)  # 5秒 < 10秒

    def test_is_execution_timeout_exceeded(self):
        timing = ExecutionTiming(start_time=100.0, end_time=115.0)
        assert is_execution_timeout(timing, 10.0)  # 15秒 > 10秒

    def test_is_execution_timeout_exact_limit(self):
        timing = ExecutionTiming(start_time=100.0, end_time=110.0)
        assert not is_execution_timeout(timing, 10.0)  # 10秒 = 10秒（not >）


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_duration(self):
        timing = ExecutionTiming(start_time=100.0, end_time=100.0)
        assert timing.duration == 0.0
        assert format_execution_timing(timing) == "0.0ms"
        assert not is_execution_timeout(timing, 0.0)

    def test_very_small_duration(self):
        timing = ExecutionTiming(start_time=100.0, end_time=100.0001)
        assert timing.duration == pytest.approx(0.0001)
        assert format_execution_timing(timing) == "0.1ms"

    def test_exactly_one_second(self):
        timing = ExecutionTiming(start_time=100.0, end_time=101.0)
        assert timing.duration == 1.0
        assert format_execution_timing(timing) == "1.00s"

    def test_exactly_sixty_seconds(self):
        timing = ExecutionTiming(start_time=100.0, end_time=160.0)
        assert timing.duration == 60.0
        assert format_execution_timing(timing) == "1m 0.0s"

    def test_negative_duration(self):
        # 通常は発生しないが、テストとして確認
        timing = ExecutionTiming(start_time=100.0, end_time=90.0)
        assert timing.duration == -10.0
        # 負の値も正常にフォーマットされる
        assert format_execution_timing(timing) == "-10000.0ms"
