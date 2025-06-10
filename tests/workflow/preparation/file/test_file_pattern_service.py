"""Tests for FilePatternService functionality."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.workflow.preparation.file.file_pattern_service import (
    FilePatternService,
    FileOperationResult
)
from src.workflow.preparation.file.exceptions import (
    ConfigValidationError,
    PatternResolutionError
)
from src.infrastructure.config.json_config_loader import JsonConfigLoader
from src.domain.interfaces.filesystem_interface import FileSystemInterface
from src.domain.interfaces.logger_interface import LoggerInterface


class TestFilePatternService:
    """Test FilePatternService functionality."""

    @pytest.fixture
    def mock_config_loader(self):
        """Mock JsonConfigLoader."""
        return Mock(spec=JsonConfigLoader)

    @pytest.fixture
    def mock_file_driver(self):
        """Mock FileDriver."""
        return Mock(spec=FileSystemInterface)

    @pytest.fixture
    def mock_logger(self):
        """Mock Logger."""
        return Mock(spec=LoggerInterface)

    @pytest.fixture
    def service(self, mock_config_loader, mock_file_driver, mock_logger):
        """Create FilePatternService instance."""
        return FilePatternService(mock_config_loader, mock_file_driver, mock_logger)

    @pytest.fixture
    def sample_file_patterns(self):
        """Sample file patterns configuration."""
        return {
            "test_files": {
                "workspace": ["test/**/*.txt", "test/**/*.in", "test/**/*.out"],
                "contest_current": ["test/"],
                "contest_stock": ["test/"]
            },
            "contest_files": {
                "workspace": ["main.cpp", "*.h"],
                "contest_current": ["main.cpp"],
                "contest_stock": ["main.cpp", "*.h"]
            }
        }

    @pytest.fixture
    def sample_file_operations(self):
        """Sample file operations configuration."""
        return {
            "move_test_files": [
                ["workspace.test_files", "contest_current.test_files"],
                ["workspace.contest_files", "contest_stock.contest_files"]
            ]
        }

    def test_get_file_patterns_success(self, service, mock_config_loader, sample_file_patterns):
        """Test successful file patterns retrieval."""
        mock_config_loader.get_language_config.return_value = {
            "file_patterns": sample_file_patterns
        }
        
        result = service.get_file_patterns("cpp")
        
        assert result == sample_file_patterns
        mock_config_loader.get_language_config.assert_called_once_with("cpp")

    def test_get_file_patterns_missing_config(self, service, mock_config_loader):
        """Test file patterns retrieval with missing configuration."""
        mock_config_loader.get_language_config.return_value = {}
        
        result = service.get_file_patterns("cpp")
        
        assert result == {}

    def test_get_file_operations_success(self, service, mock_config_loader, sample_file_operations):
        """Test successful file operations retrieval."""
        mock_config_loader.get_shared_config.return_value = {
            "file_operations": sample_file_operations
        }
        
        result = service.get_file_operations()
        
        assert result == sample_file_operations
        mock_config_loader.get_shared_config.assert_called_once()

    def test_validate_patterns_valid(self, service, sample_file_patterns):
        """Test validation of valid patterns."""
        is_valid, errors = service.validate_patterns(sample_file_patterns)
        
        assert is_valid is True
        assert errors == []

    def test_validate_patterns_invalid_structure(self, service):
        """Test validation of invalid pattern structure."""
        invalid_patterns = {
            "test_files": "not_a_dict",  # Should be dict
            "contest_files": {
                "invalid_location": ["main.cpp"],  # Invalid location
                "workspace": "not_a_list"  # Should be list
            }
        }
        
        is_valid, errors = service.validate_patterns(invalid_patterns)
        
        assert is_valid is False
        assert len(errors) == 3
        assert "Pattern group 'test_files' must be a dictionary" in errors
        assert "Invalid location 'invalid_location'" in errors[1]
        assert "Patterns for 'contest_files.workspace' must be a list" in errors[2]

    def test_validate_patterns_empty_patterns(self, service):
        """Test validation with empty patterns."""
        invalid_patterns = {
            "test_files": {
                "workspace": ["", "  ", "valid_pattern.txt"]
            }
        }
        
        is_valid, errors = service.validate_patterns(invalid_patterns)
        
        assert is_valid is False
        assert len(errors) == 2
        assert "Invalid pattern in 'test_files.workspace':" in errors[0]
        assert "Invalid pattern in 'test_files.workspace':" in errors[1]

    def test_validate_operations_valid(self, service, sample_file_operations):
        """Test validation of valid operations."""
        is_valid, errors = service.validate_operations(sample_file_operations)
        
        assert is_valid is True
        assert errors == []

    def test_validate_operations_invalid_structure(self, service):
        """Test validation of invalid operation structure."""
        invalid_operations = {
            "move_test_files": "not_a_list",  # Should be list
            "another_op": [
                ["workspace.test_files"],  # Should have 2 elements
                ["workspace.invalid", "contest_current.test_files", "extra"],  # Should have 2 elements
                ["invalid_ref", "contest_current.test_files"]  # Invalid reference format
            ]
        }
        
        is_valid, errors = service.validate_operations(invalid_operations)
        
        assert is_valid is False
        assert len(errors) == 4
        assert "Operation 'move_test_files' must be a list of steps" in errors[0]
        assert "Step 0 in operation 'another_op' must be [source, dest]" in errors[1]
        assert "Step 1 in operation 'another_op' must be [source, dest]" in errors[2]
        assert "Invalid source pattern reference: invalid_ref" in errors[3]

    def test_is_valid_pattern_reference(self, service):
        """Test pattern reference validation."""
        valid_refs = [
            "workspace.test_files",
            "contest_current.contest_files",
            "contest_stock.test_files"
        ]
        
        invalid_refs = [
            "workspace",  # Missing pattern group
            "workspace.test_files.extra",  # Too many parts
            "invalid_location.test_files",  # Invalid location
            "workspace.123invalid",  # Invalid identifier
            "workspace.",  # Empty pattern group
            ".test_files"  # Empty location
        ]
        
        for ref in valid_refs:
            assert service._is_valid_pattern_reference(ref) is True, f"Should be valid: {ref}"
        
        for ref in invalid_refs:
            assert service._is_valid_pattern_reference(ref) is False, f"Should be invalid: {ref}"

    @patch('glob.glob')
    def test_resolve_pattern_paths_success(self, mock_glob, service, mock_config_loader, sample_file_patterns):
        """Test successful pattern path resolution."""
        mock_config_loader.get_language_config.return_value = {
            "file_patterns": sample_file_patterns
        }
        mock_glob.return_value = [
            "/workspace/test/sample.txt",
            "/workspace/test/input.in",
            "/workspace/test/output.out"
        ]
        
        context = {
            "workspace_path": "/workspace",
            "language": "cpp"
        }
        
        result = service.resolve_pattern_paths("workspace.test_files", context)
        
        assert len(result) == 3
        assert all(isinstance(p, Path) for p in result)
        assert str(result[0]) == "/workspace/test/sample.txt"

    def test_resolve_pattern_paths_invalid_reference(self, service):
        """Test pattern path resolution with invalid reference."""
        context = {"workspace_path": "/workspace", "language": "cpp"}
        
        with pytest.raises(PatternResolutionError) as exc_info:
            service.resolve_pattern_paths("invalid.reference", context)
        
        assert "Invalid pattern reference format" in str(exc_info.value)

    def test_execute_file_operations_success(self, service, mock_config_loader, mock_file_driver, sample_file_patterns, sample_file_operations):
        """Test successful file operations execution."""
        # Setup mocks
        mock_config_loader.get_shared_config.return_value = {
            "file_operations": sample_file_operations
        }
        mock_config_loader.get_language_config.return_value = {
            "file_patterns": sample_file_patterns
        }
        
        # Mock file operations
        mock_file_driver.copy_file.return_value = True
        mock_file_driver.create_directory.return_value = True
        
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "contest_stock_path": "/contest_stock",
            "language": "cpp"
        }
        
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.side_effect = [
                [Path("/workspace/test/sample.txt")],  # workspace.test_files
                [Path("/workspace/main.cpp")]  # workspace.contest_files
            ]
            
            result = service.execute_file_operations("move_test_files", context)
        
        assert result.success is True
        assert result.files_processed == 2
        assert result.files_failed == 0
        assert len(result.operation_log) > 0

    def test_execute_with_fallback_config_error(self, service, mock_config_loader, mock_logger):
        """Test fallback execution when config validation fails."""
        mock_config_loader.get_shared_config.side_effect = ConfigValidationError("Invalid config")
        
        context = {"language": "cpp"}
        
        with patch.object(service, '_execute_legacy_fallback') as mock_fallback:
            mock_fallback.return_value = FileOperationResult(
                success=True,
                message="Legacy fallback successful",
                files_processed=1,
                files_failed=0,
                error_details=[],
                operation_log=["Legacy operation completed"]
            )
            
            result = service.execute_with_fallback("move_test_files", context)
        
        assert result.success is True
        assert result.message == "Legacy fallback successful"
        mock_logger.warning.assert_called_once()
        mock_fallback.assert_called_once_with(context)

    def test_diagnose_config_issues_valid_config(self, service, mock_config_loader, sample_file_patterns, sample_file_operations):
        """Test configuration diagnosis with valid config."""
        mock_config_loader.get_language_config.return_value = {
            "file_patterns": sample_file_patterns
        }
        mock_config_loader.get_shared_config.return_value = {
            "file_operations": sample_file_operations
        }
        
        with patch.object(service, '_check_required_files') as mock_check:
            mock_check.return_value = []
            
            diagnosis = service.diagnose_config_issues("cpp")
        
        assert diagnosis["language"] == "cpp"
        assert diagnosis["config_status"] == "valid"
        assert len(diagnosis["issues"]) == 0
        assert len(diagnosis["suggestions"]) == 0

    def test_diagnose_config_issues_invalid_config(self, service, mock_config_loader):
        """Test configuration diagnosis with invalid config."""
        mock_config_loader.get_language_config.return_value = {
            "file_patterns": {"invalid": "structure"}
        }
        mock_config_loader.get_shared_config.return_value = {
            "file_operations": {"invalid": "structure"}
        }
        
        with patch.object(service, '_check_required_files') as mock_check:
            mock_check.return_value = ["/missing/config.json"]
            
            diagnosis = service.diagnose_config_issues("cpp")
        
        assert diagnosis["language"] == "cpp"
        assert diagnosis["config_status"] == "invalid"
        assert len(diagnosis["issues"]) > 0
        assert len(diagnosis["suggestions"]) > 0
        assert "Fix pattern validation errors" in diagnosis["suggestions"]
        assert "Fix operation validation errors" in diagnosis["suggestions"]
        assert "Create missing configuration files" in diagnosis["suggestions"]

    def test_get_fallback_patterns(self, service):
        """Test fallback patterns generation."""
        fallback = service.get_fallback_patterns("cpp")
        
        assert "test_files" in fallback
        assert "contest_files" in fallback
        assert "workspace" in fallback["test_files"]
        assert "contest_current" in fallback["test_files"]
        assert "contest_stock" in fallback["test_files"]
        
        # Check that fallback patterns are reasonable
        assert "test/**/*.txt" in fallback["test_files"]["workspace"]
        assert "main.cpp" in fallback["contest_files"]["workspace"]


class TestFileOperationResult:
    """Test FileOperationResult functionality."""

    def test_file_operation_result_creation(self):
        """Test FileOperationResult creation and attributes."""
        result = FileOperationResult(
            success=True,
            message="Operation completed",
            files_processed=5,
            files_failed=1,
            error_details=[{"file": "test.txt", "error": "Permission denied"}],
            operation_log=["Started", "Processing", "Completed"]
        )
        
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.files_processed == 5
        assert result.files_failed == 1
        assert len(result.error_details) == 1
        assert result.error_details[0]["file"] == "test.txt"
        assert len(result.operation_log) == 3

    def test_file_operation_result_summary(self):
        """Test FileOperationResult summary information."""
        result = FileOperationResult(
            success=False,
            message="Partial failure",
            files_processed=3,
            files_failed=2,
            error_details=[
                {"file": "file1.txt", "error": "Not found"},
                {"file": "file2.txt", "error": "Permission denied"}
            ],
            operation_log=["Started", "Error occurred", "Partial completion"]
        )
        
        assert result.success is False
        assert result.files_processed == 3
        assert result.files_failed == 2
        assert len(result.error_details) == 2


class TestConfigValidationError:
    """Test ConfigValidationError exception."""

    def test_config_validation_error_creation(self):
        """Test ConfigValidationError creation."""
        error = ConfigValidationError("Invalid configuration format")
        
        assert str(error) == "Invalid configuration format"
        assert isinstance(error, Exception)


class TestPatternResolutionError:
    """Test PatternResolutionError exception."""

    def test_pattern_resolution_error_creation(self):
        """Test PatternResolutionError creation."""
        error = PatternResolutionError("Pattern not found")
        
        assert str(error) == "Pattern not found"
        assert isinstance(error, Exception)