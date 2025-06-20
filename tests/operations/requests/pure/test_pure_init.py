"""Tests for domain.requests.pure package __init__.py."""
import pytest

import src.operations.requests.pure as pure_module


class TestPurePackageInit:
    """Test the pure package initialization."""

    def test_exports_all_expected_items(self):
        """Test that all expected items are exported."""
        expected_exports = [
            'ExecutionTiming',
            'end_timing',
            'format_execution_timing',
            'is_execution_timeout',
            'start_timing'
        ]

        # Check __all__ contains expected items
        assert hasattr(pure_module, '__all__')
        assert set(pure_module.__all__) == set(expected_exports)

        # Check all items are actually importable
        for item_name in expected_exports:
            assert hasattr(pure_module, item_name), f"Missing export: {item_name}"

    def test_execution_timing_class_accessible(self):
        """Test that ExecutionTiming class is accessible."""
        assert hasattr(pure_module, 'ExecutionTiming')

        # Test basic instantiation
        timing = pure_module.ExecutionTiming(start_time=100.0)
        assert timing.start_time == 100.0
        assert timing.end_time is None

    def test_timing_functions_accessible(self):
        """Test that timing functions are accessible."""
        timing_functions = [
            'start_timing',
            'end_timing',
            'format_execution_timing',
            'is_execution_timeout'
        ]

        for func_name in timing_functions:
            assert hasattr(pure_module, func_name)
            assert callable(getattr(pure_module, func_name))

    def test_imported_items_work_correctly(self):
        """Test that imported items work as expected."""
        from unittest.mock import Mock

        # Test ExecutionTiming functionality
        timing = pure_module.ExecutionTiming(start_time=100.0, end_time=110.0)
        assert timing.duration == 10.0

        # Test format_execution_timing
        formatted = pure_module.format_execution_timing(timing)
        assert "10.00s" in formatted

        # Test is_execution_timeout
        timeout_result = pure_module.is_execution_timeout(timing, 5.0)
        assert timeout_result is True  # 10 seconds > 5 seconds

        # Test with mock time provider
        mock_time_provider = Mock()
        mock_time_provider.now.return_value = 200.0

        # Test start_timing
        start_timing_result = pure_module.start_timing(mock_time_provider)
        assert start_timing_result.start_time == 200.0

        # Test end_timing
        end_timing_result = pure_module.end_timing(start_timing_result, mock_time_provider)
        assert end_timing_result.end_time == 200.0

    def test_no_unexpected_exports(self):
        """Test that no unexpected items are exported."""
        # Get all public attributes (not starting with _)
        public_attrs = [attr for attr in dir(pure_module) if not attr.startswith('_')]

        # Filter out expected exports and module metadata
        expected = set(pure_module.__all__)
        actual_exports = set(public_attrs)

        # Should only have the declared exports (plus potentially module metadata)
        unexpected = actual_exports - expected

        # Allow common module attributes
        allowed_extras = {'timing_calculator'}  # The imported module itself
        unexpected = unexpected - allowed_extras

        assert not unexpected, f"Unexpected exports found: {unexpected}"

    def test_package_structure(self):
        """Test basic package structure."""
        # Check that the package has the expected structure
        assert hasattr(pure_module, '__file__')
        assert hasattr(pure_module, '__name__')
        assert pure_module.__name__ == 'src.operations.requests.pure'

    def test_imports_from_timing_calculator(self):
        """Test that imports come from the correct module."""
        # This test ensures the imports are actually from timing_calculator
        from src.operations.requests.pure.timing_calculator import ExecutionTiming as DirectExecutionTiming

        # Should be the same class
        assert pure_module.ExecutionTiming is DirectExecutionTiming

        # Test with a few functions as well
        from src.operations.requests.pure.timing_calculator import start_timing as direct_start_timing
        assert pure_module.start_timing is direct_start_timing
