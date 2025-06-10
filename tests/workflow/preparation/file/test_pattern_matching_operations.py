"""Tests for pattern matching and file operations functionality."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, call
import glob

from src.workflow.preparation.file.file_pattern_service import (
    FilePatternService,
    FileOperationResult
)
from src.workflow.preparation.file.exceptions import PatternResolutionError
from src.infrastructure.config.json_config_loader import JsonConfigLoader
from src.domain.interfaces.filesystem_interface import FileSystemInterface
from src.domain.interfaces.logger_interface import LoggerInterface


class TestPatternMatching:
    """Test pattern matching functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            
            # Create test directory structure
            test_dir = workspace / "test"
            test_dir.mkdir()
            
            # Create test files
            (test_dir / "sample1.txt").write_text("test data 1")
            (test_dir / "sample2.txt").write_text("test data 2")
            (test_dir / "input1.in").write_text("input data 1")
            (test_dir / "input2.in").write_text("input data 2")
            (test_dir / "output1.out").write_text("output data 1")
            (test_dir / "output2.out").write_text("output data 2")
            
            # Create subdirectory with files
            subdir = test_dir / "subdir"
            subdir.mkdir()
            (subdir / "nested.txt").write_text("nested test data")
            (subdir / "nested.in").write_text("nested input data")
            
            # Create main files
            (workspace / "main.cpp").write_text("int main() { return 0; }")
            (workspace / "helper.h").write_text("#ifndef HELPER_H")
            (workspace / "utils.hpp").write_text("#pragma once")
            
            # Create build artifacts
            build_dir = workspace / "build"
            build_dir.mkdir()
            (build_dir / "main.o").write_text("object file")
            (workspace / "main.exe").write_text("executable")
            
            yield workspace

    @pytest.fixture
    def mock_config_loader(self):
        """Mock JsonConfigLoader with test patterns."""
        mock = Mock(spec=JsonConfigLoader)
        mock.get_language_config.return_value = {
            "file_patterns": {
                "test_files": {
                    "workspace": ["test/**/*.txt", "test/**/*.in", "test/**/*.out"],
                    "contest_current": ["test/"],
                    "contest_stock": ["test/"]
                },
                "contest_files": {
                    "workspace": ["main.cpp", "*.h", "*.hpp"],
                    "contest_current": ["main.cpp"],
                    "contest_stock": ["main.cpp", "*.h", "*.hpp"]
                },
                "build_files": {
                    "workspace": ["build/**/*", "*.o", "*.exe"],
                    "contest_current": [],
                    "contest_stock": []
                }
            }
        }
        return mock

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

    def test_resolve_pattern_paths_test_files(self, service, temp_workspace):
        """Test resolving test file patterns."""
        context = {
            "workspace_path": str(temp_workspace),
            "language": "cpp"
        }
        
        with patch('os.getcwd', return_value=str(temp_workspace)):
            paths = service.resolve_pattern_paths("workspace.test_files", context)
        
        path_strings = [str(p) for p in paths]
        
        # Should find all test files including nested ones
        assert any("sample1.txt" in p for p in path_strings)
        assert any("sample2.txt" in p for p in path_strings)
        assert any("input1.in" in p for p in path_strings)
        assert any("input2.in" in p for p in path_strings)
        assert any("output1.out" in p for p in path_strings)
        assert any("output2.out" in p for p in path_strings)
        assert any("nested.txt" in p for p in path_strings)
        assert any("nested.in" in p for p in path_strings)

    def test_resolve_pattern_paths_contest_files(self, service, temp_workspace):
        """Test resolving contest file patterns."""
        context = {
            "workspace_path": str(temp_workspace),
            "language": "cpp"
        }
        
        with patch('os.getcwd', return_value=str(temp_workspace)):
            paths = service.resolve_pattern_paths("workspace.contest_files", context)
        
        path_strings = [str(p) for p in paths]
        
        # Should find main.cpp and header files
        assert any("main.cpp" in p for p in path_strings)
        assert any("helper.h" in p for p in path_strings)
        assert any("utils.hpp" in p for p in path_strings)

    def test_resolve_pattern_paths_build_files(self, service, temp_workspace):
        """Test resolving build file patterns."""
        context = {
            "workspace_path": str(temp_workspace),
            "language": "cpp"
        }
        
        with patch('os.getcwd', return_value=str(temp_workspace)):
            paths = service.resolve_pattern_paths("workspace.build_files", context)
        
        path_strings = [str(p) for p in paths]
        
        # Should find build artifacts
        assert any("main.o" in p for p in path_strings)
        assert any("main.exe" in p for p in path_strings)

    def test_resolve_pattern_paths_empty_patterns(self, service, mock_config_loader):
        """Test resolving empty pattern list."""
        mock_config_loader.get_language_config.return_value = {
            "file_patterns": {
                "empty_group": {
                    "workspace": [],
                    "contest_current": [],
                    "contest_stock": []
                }
            }
        }
        
        context = {
            "workspace_path": "/workspace",
            "language": "cpp"
        }
        
        paths = service.resolve_pattern_paths("workspace.empty_group", context)
        
        assert paths == []

    def test_resolve_pattern_paths_no_matches(self, service, temp_workspace):
        """Test resolving patterns with no matching files."""
        # Add pattern that won't match anything
        service.config_loader.get_language_config.return_value = {
            "file_patterns": {
                "nonexistent_files": {
                    "workspace": ["**/*.xyz", "nonexistent/**/*"],
                    "contest_current": [],
                    "contest_stock": []
                }
            }
        }
        
        context = {
            "workspace_path": str(temp_workspace),
            "language": "cpp"
        }
        
        with patch('os.getcwd', return_value=str(temp_workspace)):
            paths = service.resolve_pattern_paths("workspace.nonexistent_files", context)
        
        assert paths == []

    def test_resolve_pattern_paths_invalid_reference_format(self, service):
        """Test resolving with invalid pattern reference format."""
        context = {
            "workspace_path": "/workspace",
            "language": "cpp"
        }
        
        invalid_refs = [
            "workspace",  # Missing pattern group
            "workspace.test_files.extra",  # Too many parts
            "invalid_location.test_files",  # Invalid location
            "",  # Empty reference
            "workspace."  # Empty pattern group
        ]
        
        for ref in invalid_refs:
            with pytest.raises(PatternResolutionError) as exc_info:
                service.resolve_pattern_paths(ref, context)
            assert "Invalid pattern reference format" in str(exc_info.value)

    def test_resolve_pattern_paths_nonexistent_pattern_group(self, service):
        """Test resolving with non-existent pattern group."""
        context = {
            "workspace_path": "/workspace",
            "language": "cpp"
        }
        
        with pytest.raises(PatternResolutionError) as exc_info:
            service.resolve_pattern_paths("workspace.nonexistent_group", context)
        
        assert "Pattern group 'nonexistent_group' not found" in str(exc_info.value)

    def test_resolve_pattern_paths_nonexistent_location(self, service):
        """Test resolving with non-existent location."""
        context = {
            "workspace_path": "/workspace",
            "language": "cpp"
        }
        
        with pytest.raises(PatternResolutionError) as exc_info:
            service.resolve_pattern_paths("nonexistent_location.test_files", context)
        
        assert "Location 'nonexistent_location' not found" in str(exc_info.value)


class TestFileOperations:
    """Test file operations functionality."""

    @pytest.fixture
    def mock_config_loader(self):
        """Mock JsonConfigLoader with operations."""
        mock = Mock(spec=JsonConfigLoader)
        mock.get_shared_config.return_value = {
            "file_operations": {
                "move_test_files": [
                    ["workspace.test_files", "contest_current.test_files"],
                    ["workspace.contest_files", "contest_stock.contest_files"]
                ],
                "cleanup_workspace": [
                    ["workspace.build_files", "contest_stock.build_files"]
                ]
            }
        }
        mock.get_language_config.return_value = {
            "file_patterns": {
                "test_files": {
                    "workspace": ["test/**/*.txt", "test/**/*.in"],
                    "contest_current": ["test/"],
                    "contest_stock": ["test/"]
                },
                "contest_files": {
                    "workspace": ["main.cpp", "*.h"],
                    "contest_current": ["main.cpp"],
                    "contest_stock": ["main.cpp", "*.h"]
                },
                "build_files": {
                    "workspace": ["build/**/*", "*.o"],
                    "contest_current": [],
                    "contest_stock": []
                }
            }
        }
        return mock

    @pytest.fixture
    def mock_file_driver(self):
        """Mock FileDriver with successful operations."""
        mock = Mock(spec=FileSystemInterface)
        mock.copy_file.return_value = True
        mock.move_file.return_value = True
        mock.create_directory.return_value = True
        mock.delete_file.return_value = True
        return mock

    @pytest.fixture
    def mock_logger(self):
        """Mock Logger."""
        return Mock(spec=LoggerInterface)

    @pytest.fixture
    def service(self, mock_config_loader, mock_file_driver, mock_logger):
        """Create FilePatternService instance."""
        return FilePatternService(mock_config_loader, mock_file_driver, mock_logger)

    def test_execute_file_operations_move_test_files(self, service):
        """Test executing move_test_files operation."""
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "contest_stock_path": "/contest_stock",
            "language": "cpp"
        }
        
        # Mock pattern resolution
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.side_effect = [
                [Path("/workspace/test/file1.txt"), Path("/workspace/test/file2.in")],  # workspace.test_files
                [Path("/workspace/main.cpp"), Path("/workspace/helper.h")]  # workspace.contest_files
            ]
            
            result = service.execute_file_operations("move_test_files", context)
        
        assert result.success is True
        assert result.files_processed == 4
        assert result.files_failed == 0
        
        # Check that file operations were called
        assert service.file_driver.copy_file.call_count == 4
        
        # Verify the calls
        expected_calls = [
            call(Path("/workspace/test/file1.txt"), Path("/contest_current/test/file1.txt")),
            call(Path("/workspace/test/file2.in"), Path("/contest_current/test/file2.in")),
            call(Path("/workspace/main.cpp"), Path("/contest_stock/main.cpp")),
            call(Path("/workspace/helper.h"), Path("/contest_stock/helper.h"))
        ]
        service.file_driver.copy_file.assert_has_calls(expected_calls, any_order=True)

    def test_execute_file_operations_cleanup_workspace(self, service):
        """Test executing cleanup_workspace operation."""
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "contest_stock_path": "/contest_stock",
            "language": "cpp"
        }
        
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.return_value = [
                Path("/workspace/build/main.o"),
                Path("/workspace/temp.o")
            ]
            
            result = service.execute_file_operations("cleanup_workspace", context)
        
        assert result.success is True
        assert result.files_processed == 2
        assert result.files_failed == 0
        
        # Check file operations
        assert service.file_driver.copy_file.call_count == 2

    def test_execute_file_operations_partial_failure(self, service, mock_file_driver):
        """Test executing operations with partial failures."""
        # Setup file driver to fail some operations
        mock_file_driver.copy_file.side_effect = [True, False, True, False]
        
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "contest_stock_path": "/contest_stock",
            "language": "cpp"
        }
        
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.side_effect = [
                [Path("/workspace/test/file1.txt"), Path("/workspace/test/file2.in")],
                [Path("/workspace/main.cpp"), Path("/workspace/helper.h")]
            ]
            
            result = service.execute_file_operations("move_test_files", context)
        
        assert result.success is False  # Overall failure due to partial failures
        assert result.files_processed == 2  # 2 successful operations
        assert result.files_failed == 2  # 2 failed operations
        assert len(result.error_details) == 2
        
        # Check error details
        error_files = [error["file"] for error in result.error_details]
        assert "/workspace/test/file2.in" in error_files
        assert "/workspace/helper.h" in error_files

    def test_execute_file_operations_nonexistent_operation(self, service):
        """Test executing non-existent operation."""
        context = {
            "workspace_path": "/workspace",
            "language": "cpp"
        }
        
        result = service.execute_file_operations("nonexistent_operation", context)
        
        assert result.success is False
        assert "Operation 'nonexistent_operation' not found" in result.message

    def test_execute_file_operations_pattern_resolution_error(self, service):
        """Test executing operations with pattern resolution errors."""
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "language": "cpp"
        }
        
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.side_effect = PatternResolutionError("Pattern not found")
            
            result = service.execute_file_operations("move_test_files", context)
        
        assert result.success is False
        assert "Pattern not found" in result.message

    def test_execute_file_operations_empty_patterns(self, service):
        """Test executing operations with empty pattern results."""
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "contest_stock_path": "/contest_stock",
            "language": "cpp"
        }
        
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.return_value = []  # No files found
            
            result = service.execute_file_operations("move_test_files", context)
        
        assert result.success is True
        assert result.files_processed == 0
        assert result.files_failed == 0
        assert "No files found for patterns" in result.message

    def test_execute_file_operations_directory_creation(self, service, mock_file_driver):
        """Test that directories are created as needed."""
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "contest_stock_path": "/contest_stock",
            "language": "cpp"
        }
        
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.side_effect = [
                [Path("/workspace/test/nested/file.txt")],
                []
            ]
            
            result = service.execute_file_operations("move_test_files", context)
        
        # Should create parent directory
        mock_file_driver.create_directory.assert_called_with(Path("/contest_current/test/nested"))
        assert result.success is True

    def test_file_operation_logging(self, service, mock_logger):
        """Test that file operations are properly logged."""
        context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "language": "cpp"
        }
        
        with patch.object(service, 'resolve_pattern_paths') as mock_resolve:
            mock_resolve.side_effect = [
                [Path("/workspace/test/file.txt")],
                []
            ]
            
            result = service.execute_file_operations("move_test_files", context)
        
        # Check that operations were logged
        assert len(result.operation_log) > 0
        assert any("Started operation: move_test_files" in log for log in result.operation_log)
        assert any("Processing step 1/2" in log for log in result.operation_log)


class TestPatternUtilities:
    """Test pattern utility functions."""

    @pytest.fixture
    def service(self):
        """Create minimal service for utility testing."""
        mock_config = Mock(spec=JsonConfigLoader)
        mock_file = Mock(spec=FilesystemInterface)
        mock_logger = Mock(spec=LoggerInterface)
        return FilePatternService(mock_config, mock_file, mock_logger)

    def test_normalize_pattern_paths(self, service):
        """Test pattern path normalization."""
        # Test various path formats
        test_cases = [
            ("test/**/*.txt", "test/**/*.txt"),  # Already normalized
            ("test\\**\\*.txt", "test/**/*.txt"),  # Windows backslashes
            ("./test/**/*.txt", "test/**/*.txt"),  # Relative current dir
            ("test//*.txt", "test/*.txt"),  # Double slashes
            ("test/", "test/"),  # Directory pattern
        ]
        
        for input_pattern, expected in test_cases:
            normalized = service._normalize_pattern(input_pattern)
            assert normalized == expected, f"Expected {expected}, got {normalized} for input {input_pattern}"

    def test_get_destination_path(self, service):
        """Test destination path calculation."""
        test_cases = [
            (
                Path("/workspace/test/file.txt"),
                Path("/workspace"),
                Path("/contest_current"),
                Path("/contest_current/test/file.txt")
            ),
            (
                Path("/workspace/main.cpp"),
                Path("/workspace"),
                Path("/contest_stock"),
                Path("/contest_stock/main.cpp")
            ),
            (
                Path("/workspace/nested/deep/file.h"),
                Path("/workspace"),
                Path("/contest_current"),
                Path("/contest_current/nested/deep/file.h")
            ),
        ]
        
        for source, source_base, dest_base, expected in test_cases:
            result = service._get_destination_path(source, source_base, dest_base)
            assert result == expected

    def test_is_file_excluded(self, service):
        """Test file exclusion logic."""
        # Mock common exclusion patterns
        excluded_patterns = ["*.tmp", "*.log", "__pycache__/**/*", ".git/**/*"]
        
        test_cases = [
            ("file.txt", False),
            ("temp.tmp", True),
            ("debug.log", True),
            ("__pycache__/module.pyc", True),
            (".git/config", True),
            ("test/__pycache__/cache.pyc", True),
            ("regular_file.py", False),
        ]
        
        with patch.object(service, '_get_exclusion_patterns', return_value=excluded_patterns):
            for file_path, should_be_excluded in test_cases:
                result = service._is_file_excluded(Path(file_path))
                assert result == should_be_excluded, f"File {file_path} exclusion check failed"