"""Tests for execution types."""
import pytest

from src.operations.types.execution_types import (
    ExecutionResult,
    ExecutionStatus,
    TestResult,
    TestStatus,
)


class TestExecutionStatus:
    """Test ExecutionStatus enum."""

    def test_execution_status_values(self):
        assert ExecutionStatus.PASS.value == "PASS"
        assert ExecutionStatus.FAIL.value == "FAIL"
        assert ExecutionStatus.ERROR.value == "ERROR"
        assert ExecutionStatus.SKIP.value == "SKIP"

    def test_execution_status_enum_members(self):
        statuses = list(ExecutionStatus)
        assert len(statuses) == 4
        assert ExecutionStatus.PASS in statuses
        assert ExecutionStatus.FAIL in statuses
        assert ExecutionStatus.ERROR in statuses
        assert ExecutionStatus.SKIP in statuses

    def test_test_status_alias(self):
        assert TestStatus is ExecutionStatus
        assert TestStatus.PASS == ExecutionStatus.PASS


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_minimal_execution_result(self):
        result = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.PASS
        )
        assert result.test_name == "test_example"
        assert result.status == ExecutionStatus.PASS
        assert result.expected_output is None
        assert result.actual_output is None
        assert result.error_message is None
        assert result.execution_time is None

    def test_full_execution_result(self):
        result = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.FAIL,
            expected_output="expected",
            actual_output="actual",
            error_message="Test failed",
            execution_time=1.23
        )
        assert result.test_name == "test_example"
        assert result.status == ExecutionStatus.FAIL
        assert result.expected_output == "expected"
        assert result.actual_output == "actual"
        assert result.error_message == "Test failed"
        assert result.execution_time == 1.23


    def test_execution_result_equality(self):
        result1 = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.PASS
        )
        result2 = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.PASS
        )
        result3 = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.FAIL
        )
        assert result1 == result2
        assert result1 != result3

    def test_test_result_alias(self):
        assert TestResult is ExecutionResult
        result = TestResult(
            test_name="test_example",
            status=TestStatus.PASS
        )
        assert isinstance(result, ExecutionResult)

    def test_execution_result_with_different_statuses(self):
        test_cases = [
            (ExecutionStatus.PASS, None),
            (ExecutionStatus.FAIL, "Assertion failed"),
            (ExecutionStatus.ERROR, "Runtime error"),
            (ExecutionStatus.SKIP, "Test skipped"),
        ]

        for status, error_msg in test_cases:
            result = ExecutionResult(
                test_name=f"test_{status.value.lower()}",
                status=status,
                error_message=error_msg
            )
            assert result.status == status
            assert result.error_message == error_msg

    def test_execution_result_str_representation(self):
        result = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.PASS
        )
        str_repr = str(result)
        assert "test_example" in str_repr
        assert "PASS" in str_repr

    def test_execution_time_types(self):
        result_with_int = ExecutionResult(
            test_name="test_int_time",
            status=ExecutionStatus.PASS,
            execution_time=1
        )
        result_with_float = ExecutionResult(
            test_name="test_float_time",
            status=ExecutionStatus.PASS,
            execution_time=1.5
        )
        assert result_with_int.execution_time == 1
        assert result_with_float.execution_time == 1.5
