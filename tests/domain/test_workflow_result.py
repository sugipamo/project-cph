"""Tests for workflow result data structures"""
import pytest
from src.domain.workflow_result import WorkflowExecutionResult
from src.operations.results.result import OperationResult


class TestWorkflowExecutionResult:
    """Test cases for WorkflowExecutionResult"""

    def test_initialization_with_all_fields(self):
        """Test creating WorkflowExecutionResult with all fields"""
        operation_result1 = OperationResult(
            success=True,
            message="Operation 1 completed",
            details={"key": "value"},
            error_code=None
        )
        operation_result2 = OperationResult(
            success=False,
            message="Operation 2 failed",
            details=None,
            error_code="OP_FAILED"
        )
        preparation_result = OperationResult(
            success=True,
            message="Preparation completed",
            details={"prepared": True},
            error_code=None
        )
        
        result = WorkflowExecutionResult(
            success=True,
            results=[operation_result1, operation_result2],
            preparation_results=[preparation_result],
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        
        assert result.success is True
        assert len(result.results) == 2
        assert result.results[0] == operation_result1
        assert result.results[1] == operation_result2
        assert len(result.preparation_results) == 1
        assert result.preparation_results[0] == preparation_result
        assert result.errors == ["Error 1", "Error 2"]
        assert result.warnings == ["Warning 1"]

    def test_initialization_with_empty_lists(self):
        """Test creating WorkflowExecutionResult with empty lists"""
        result = WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        
        assert result.success is False
        assert result.results == []
        assert result.preparation_results == []
        assert result.errors == []
        assert result.warnings == []

    def test_failed_workflow_with_errors(self):
        """Test a failed workflow execution with errors"""
        failed_operation = OperationResult(
            success=False,
            message="Critical failure",
            details=None,
            error_code="CRITICAL_ERROR"
        )
        
        result = WorkflowExecutionResult(
            success=False,
            results=[failed_operation],
            preparation_results=[],
            errors=["Database connection failed", "File not found"],
            warnings=[]
        )
        
        assert result.success is False
        assert len(result.results) == 1
        assert result.results[0].success is False
        assert len(result.errors) == 2
        assert "Database connection failed" in result.errors
        assert "File not found" in result.errors
        assert result.warnings == []

    def test_successful_workflow_with_warnings(self):
        """Test a successful workflow execution with warnings"""
        successful_operation = OperationResult(
            success=True,
            message="Operation completed with warnings",
            details={"processed": 100},
            error_code=None
        )
        
        result = WorkflowExecutionResult(
            success=True,
            results=[successful_operation],
            preparation_results=[],
            errors=[],
            warnings=["Cache miss", "Slow query detected"]
        )
        
        assert result.success is True
        assert len(result.warnings) == 2
        assert "Cache miss" in result.warnings
        assert "Slow query detected" in result.warnings
        assert result.errors == []

    def test_workflow_with_multiple_preparation_results(self):
        """Test workflow with multiple preparation steps"""
        prep1 = OperationResult(success=True, message="Env setup done", details=None, error_code=None)
        prep2 = OperationResult(success=True, message="Config loaded", details=None, error_code=None)
        prep3 = OperationResult(success=True, message="Resources allocated", details=None, error_code=None)
        
        main_result = OperationResult(success=True, message="Main task done", details=None, error_code=None)
        
        result = WorkflowExecutionResult(
            success=True,
            results=[main_result],
            preparation_results=[prep1, prep2, prep3],
            errors=[],
            warnings=[]
        )
        
        assert len(result.preparation_results) == 3
        assert all(r.success for r in result.preparation_results)
        assert result.preparation_results[0].message == "Env setup done"
        assert result.preparation_results[1].message == "Config loaded"
        assert result.preparation_results[2].message == "Resources allocated"

    def test_dataclass_equality(self):
        """Test dataclass equality comparison"""
        operation = OperationResult(success=True, message="Test", details=None, error_code=None)
        
        result1 = WorkflowExecutionResult(
            success=True,
            results=[operation],
            preparation_results=[],
            errors=["error"],
            warnings=["warning"]
        )
        
        result2 = WorkflowExecutionResult(
            success=True,
            results=[operation],
            preparation_results=[],
            errors=["error"],
            warnings=["warning"]
        )
        
        result3 = WorkflowExecutionResult(
            success=False,  # Different success value
            results=[operation],
            preparation_results=[],
            errors=["error"],
            warnings=["warning"]
        )
        
        assert result1 == result2
        assert result1 != result3

    def test_mixed_success_results(self):
        """Test workflow with mixed success/failure operations"""
        success_op = OperationResult(success=True, message="Step 1 OK", details=None, error_code=None)
        failure_op = OperationResult(success=False, message="Step 2 failed", details=None, error_code="STEP2_FAIL")
        recovery_op = OperationResult(success=True, message="Step 3 recovered", details=None, error_code=None)
        
        result = WorkflowExecutionResult(
            success=False,  # Overall failure due to step 2
            results=[success_op, failure_op, recovery_op],
            preparation_results=[],
            errors=["Step 2 critical failure"],
            warnings=["Recovery attempted"]
        )
        
        assert result.success is False
        assert len(result.results) == 3
        assert result.results[0].success is True
        assert result.results[1].success is False
        assert result.results[2].success is True
        assert len(result.errors) == 1
        assert len(result.warnings) == 1