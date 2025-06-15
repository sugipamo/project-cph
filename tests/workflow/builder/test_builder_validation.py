"""Tests for builder validation module."""
import pytest

from src.workflow.builder.builder_validation import (
    ValidationResult,
    create_validation_report
)


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_init_basic(self):
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1"],
            statistics={"count": 5}
        )
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == ["Warning 1"]
        assert result.suggestions == ["Suggestion 1"]
        assert result.statistics == {"count": 5}
    
    def test_immutability(self):
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            statistics={}
        )
        
        # frozen=True prevents attribute modification
        with pytest.raises(AttributeError):
            result.is_valid = False
        
        with pytest.raises(AttributeError):
            result.errors = ["New error"]
    
    def test_success_factory_minimal(self):
        result = ValidationResult.success()
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []
        assert result.statistics == {}
    
    def test_success_factory_with_warnings(self):
        result = ValidationResult.success(
            warnings=["Warning 1", "Warning 2"],
            suggestions=["Suggestion 1"],
            statistics={"total": 10, "processed": 8}
        )
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == ["Warning 1", "Warning 2"]
        assert result.suggestions == ["Suggestion 1"]
        assert result.statistics == {"total": 10, "processed": 8}
    
    def test_failure_factory_minimal(self):
        result = ValidationResult.failure(errors=["Error 1", "Error 2"])
        
        assert result.is_valid is False
        assert result.errors == ["Error 1", "Error 2"]
        assert result.warnings == []
        assert result.suggestions == []
        assert result.statistics == {}
    
    def test_failure_factory_full(self):
        result = ValidationResult.failure(
            errors=["Critical error"],
            warnings=["Minor issue"],
            suggestions=["Try this instead"],
            statistics={"failed_nodes": 3}
        )
        
        assert result.is_valid is False
        assert result.errors == ["Critical error"]
        assert result.warnings == ["Minor issue"]
        assert result.suggestions == ["Try this instead"]
        assert result.statistics == {"failed_nodes": 3}


class TestCreateValidationReport:
    """Test create_validation_report function."""
    
    def test_empty_results(self):
        report = create_validation_report([])
        assert report == "No validation results provided"
    
    def test_single_success_result(self):
        result = ValidationResult.success()
        report = create_validation_report([result])
        
        assert "=== Validation Report ===" in report
        assert "--- Validation 1 ---" in report
        assert "Status: PASS" in report
        assert "=== Summary ===" in report
        assert "Total validations: 1" in report
        assert "Passed: 1" in report
        assert "Failed: 0" in report
        assert "Total errors: 0" in report
        assert "Total warnings: 0" in report
    
    def test_single_failure_result(self):
        result = ValidationResult.failure(
            errors=["Connection error", "Invalid node"]
        )
        report = create_validation_report([result])
        
        assert "Status: FAIL" in report
        assert "Errors:" in report
        assert "  - Connection error" in report
        assert "  - Invalid node" in report
        assert "Total errors: 2" in report
        assert "Failed: 1" in report
    
    def test_multiple_mixed_results(self):
        results = [
            ValidationResult.success(warnings=["Minor warning"]),
            ValidationResult.failure(
                errors=["Critical failure"],
                warnings=["Another warning"],
                suggestions=["Fix the connection"]
            ),
            ValidationResult.success(
                suggestions=["Optimize performance"],
                statistics={"nodes": 5, "edges": 4}
            )
        ]
        
        report = create_validation_report(results)
        
        # Check each validation section
        assert "--- Validation 1 ---" in report
        assert "--- Validation 2 ---" in report
        assert "--- Validation 3 ---" in report
        
        # Check warnings section
        assert "Warnings:" in report
        assert "  - Minor warning" in report
        assert "  - Another warning" in report
        
        # Check errors section
        assert "Errors:" in report
        assert "  - Critical failure" in report
        
        # Check suggestions section
        assert "Suggestions:" in report
        assert "  - Fix the connection" in report
        assert "  - Optimize performance" in report
        
        # Check statistics section
        assert "Statistics:" in report
        assert "  nodes: 5" in report
        assert "  edges: 4" in report
        
        # Check summary
        assert "Total validations: 3" in report
        assert "Passed: 2" in report
        assert "Failed: 1" in report
        assert "Total errors: 1" in report
        assert "Total warnings: 2" in report
    
    def test_report_formatting(self):
        results = [
            ValidationResult.failure(
                errors=["Error 1", "Error 2", "Error 3"],
                warnings=["Warning 1"]
            ),
            ValidationResult.success(
                warnings=["Warning 2", "Warning 3"],
                suggestions=["Suggestion 1", "Suggestion 2"],
                statistics={
                    "total_nodes": 10,
                    "valid_nodes": 8,
                    "execution_time": 1.23
                }
            )
        ]
        
        report = create_validation_report(results)
        lines = report.split('\n')
        
        # Check structure
        assert lines[0] == "=== Validation Report ==="
        assert any("--- Validation 1 ---" in line for line in lines)
        assert any("--- Validation 2 ---" in line for line in lines)
        assert any("=== Summary ===" in line for line in lines)
        
        # Count occurrences
        assert sum(1 for line in lines if line.startswith("  - ")) == 8  # 3 errors + 3 warnings + 2 suggestions
        assert sum(1 for line in lines if line.startswith("  ") and ":" in line) == 3  # 3 statistics
    
    def test_large_validation_results(self):
        # Test with many validation results
        results = []
        for i in range(10):
            if i % 2 == 0:
                results.append(ValidationResult.success(
                    warnings=[f"Warning {i}"],
                    statistics={"index": i}
                ))
            else:
                results.append(ValidationResult.failure(
                    errors=[f"Error {i}-1", f"Error {i}-2"]
                ))
        
        report = create_validation_report(results)
        
        # Check all validations are included
        for i in range(10):
            assert f"--- Validation {i+1} ---" in report
        
        # Check totals
        assert "Total validations: 10" in report
        assert "Passed: 5" in report
        assert "Failed: 5" in report
        assert "Total errors: 10" in report  # 5 failures × 2 errors each
        assert "Total warnings: 5" in report  # 5 successes × 1 warning each