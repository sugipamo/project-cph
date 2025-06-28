"""Tests for execution types"""
import pytest
from src.application.execution_types import ExecutionStatus, ExecutionResult, TestStatus, TestResult


class TestExecutionStatus:
    """Test ExecutionStatus enum"""
    
    def test_enum_values(self):
        """Test enum values are correctly defined"""
        assert ExecutionStatus.PASS.value == "PASS"
        assert ExecutionStatus.FAIL.value == "FAIL"
        assert ExecutionStatus.ERROR.value == "ERROR"
        assert ExecutionStatus.SKIP.value == "SKIP"
    
    def test_enum_members(self):
        """Test all enum members exist"""
        members = list(ExecutionStatus)
        assert len(members) == 4
        assert ExecutionStatus.PASS in members
        assert ExecutionStatus.FAIL in members
        assert ExecutionStatus.ERROR in members
        assert ExecutionStatus.SKIP in members


class TestExecutionResult:
    """Test ExecutionResult dataclass"""
    
    def test_creation_minimal(self):
        """Test creating ExecutionResult with minimal params"""
        result = ExecutionResult(
            test_name="test1",
            status=ExecutionStatus.PASS
        )
        assert result.test_name == "test1"
        assert result.status == ExecutionStatus.PASS
        assert result.expected_output is None
        assert result.actual_output is None
        assert result.error_message is None
        assert result.execution_time is None
    
    def test_creation_full(self):
        """Test creating ExecutionResult with all params"""
        result = ExecutionResult(
            test_name="test2",
            status=ExecutionStatus.FAIL,
            expected_output="expected",
            actual_output="actual",
            error_message="error",
            execution_time=1.5
        )
        assert result.test_name == "test2"
        assert result.status == ExecutionStatus.FAIL
        assert result.expected_output == "expected"
        assert result.actual_output == "actual"
        assert result.error_message == "error"
        assert result.execution_time == 1.5
    
    def test_frozen_dataclass(self):
        """Test that ExecutionResult is frozen"""
        result = ExecutionResult(
            test_name="test3",
            status=ExecutionStatus.ERROR
        )
        with pytest.raises(AttributeError):
            result.test_name = "modified"
    
    def test_equality(self):
        """Test ExecutionResult equality"""
        result1 = ExecutionResult(
            test_name="test4",
            status=ExecutionStatus.PASS,
            execution_time=1.0
        )
        result2 = ExecutionResult(
            test_name="test4",
            status=ExecutionStatus.PASS,
            execution_time=1.0
        )
        result3 = ExecutionResult(
            test_name="test4",
            status=ExecutionStatus.FAIL,
            execution_time=1.0
        )
        assert result1 == result2
        assert result1 != result3


class TestBackwardCompatibility:
    """Test backward compatibility aliases"""
    
    def test_test_status_alias(self):
        """Test TestStatus is alias for ExecutionStatus"""
        assert TestStatus is ExecutionStatus
        assert TestStatus.PASS == ExecutionStatus.PASS
        assert TestStatus.FAIL == ExecutionStatus.FAIL
        assert TestStatus.ERROR == ExecutionStatus.ERROR
        assert TestStatus.SKIP == ExecutionStatus.SKIP
    
    def test_test_result_alias(self):
        """Test TestResult is alias for ExecutionResult"""
        assert TestResult is ExecutionResult
        
        # Create using alias
        result = TestResult(
            test_name="test5",
            status=TestStatus.PASS
        )
        assert isinstance(result, ExecutionResult)
        assert result.test_name == "test5"
        assert result.status == ExecutionStatus.PASS