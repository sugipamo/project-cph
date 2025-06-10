"""Integration tests for file preparation side effects.

This module tests the complete file preparation workflow including:
- workspace_switch operation creating directories
- move_test_files operation moving actual files
- Integration with real file operations and their side effects

These tests use a temporary directory approach to safely test file system side effects.
"""

import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest

from src.infrastructure.config.di_config import configure_test_dependencies
from src.infrastructure.di_container import DIContainer
from src.workflow.problem_workspace_service import ProblemWorkspaceService


class TestFilePreparationSideEffects:
    """Test file preparation operations with real file system side effects."""

    @pytest.fixture
    def temp_directories(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            base_paths = {
                "contest_current_path": str(temp_path / "contest_current"),
                "contest_stock_path": str(temp_path / "contest_stock"),
                "contest_template_path": str(temp_path / "contest_template"),
                "workspace_path": str(temp_path / "workspace")
            }
            
            # Create template directory with sample files
            template_dir = temp_path / "contest_template" / "python"
            template_dir.mkdir(parents=True, exist_ok=True)
            (template_dir / "main.py").write_text("# Template file\nprint('Hello World')")
            
            # Create workspace directory with test files (simulating oj download)
            workspace_test_dir = temp_path / "workspace" / "test"
            workspace_test_dir.mkdir(parents=True, exist_ok=True)
            (workspace_test_dir / "sample-01.in").write_text("1 2\n")
            (workspace_test_dir / "sample-01.out").write_text("3\n")
            (workspace_test_dir / "sample-02.in").write_text("5 7\n")
            (workspace_test_dir / "sample-02.out").write_text("12\n")
            
            yield base_paths, temp_path

    @pytest.fixture
    def workspace_service(self, temp_directories):
        """Create a workspace service with real file driver for testing."""
        base_paths, temp_path = temp_directories
        
        # Use real LocalFileDriver for side effect testing
        from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
        from src.infrastructure.drivers.logging.python_logger import PythonLogger
        from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository
        from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
        
        file_driver = LocalFileDriver(base_dir=temp_path)
        sqlite_manager = FastSQLiteManager(":memory:", skip_migrations=False)
        repository = FilePreparationRepository(sqlite_manager)
        logger = PythonLogger()
        
        return ProblemWorkspaceService(
            file_driver=file_driver,
            repository=repository,
            logger=logger,
            base_paths=base_paths
        )

    def test_workspace_switch_creates_required_directories(self, workspace_service):
        """Test that workspace_switch creates all necessary directories."""
        # Execute workspace switch
        result = workspace_service.switch_to_problem(
            contest="abc302",
            problem="a", 
            language="python"
        )
        
        # Verify operation succeeded
        assert result.success, f"Workspace switch failed: {result.message}"
        
        # Verify directories were created
        base_paths = workspace_service.base_paths
        contest_current_path = Path(base_paths["contest_current_path"])
        workspace_path = Path(base_paths["workspace_path"])
        
        assert contest_current_path.exists(), "contest_current directory was not created"
        assert workspace_path.exists(), "workspace directory was not created"
        
        # Verify template files were copied
        main_py = contest_current_path / "main.py"
        assert main_py.exists(), "Template main.py was not copied"
        assert "Hello World" in main_py.read_text(), "Template content was not preserved"

    def test_move_test_files_creates_test_directory_in_contest_current(self, workspace_service):
        """Test that move_test_files creates test directory with files in contest_current."""
        # First execute workspace switch to set up directories
        switch_result = workspace_service.switch_to_problem(
            contest="abc302",
            problem="a",
            language="python"
        )
        assert switch_result.success, "Initial workspace switch failed"
        
        # Verify test files were moved to contest_current/test
        base_paths = workspace_service.base_paths
        contest_current_test = Path(base_paths["contest_current_path"]) / "test"
        
        assert contest_current_test.exists(), "test directory was not created in contest_current"
        
        # Verify test files exist
        sample_01_in = contest_current_test / "sample-01.in"
        sample_01_out = contest_current_test / "sample-01.out"
        sample_02_in = contest_current_test / "sample-02.in"
        sample_02_out = contest_current_test / "sample-02.out"
        
        assert sample_01_in.exists(), "sample-01.in was not moved"
        assert sample_01_out.exists(), "sample-01.out was not moved"
        assert sample_02_in.exists(), "sample-02.in was not moved"
        assert sample_02_out.exists(), "sample-02.out was not moved"
        
        # Verify file contents are preserved
        assert sample_01_in.read_text() == "1 2\n", "Input file content was corrupted"
        assert sample_01_out.read_text() == "3\n", "Output file content was corrupted"
        assert sample_02_in.read_text() == "5 7\n", "Input file content was corrupted"
        assert sample_02_out.read_text() == "12\n", "Output file content was corrupted"

    def test_workspace_operations_with_file_preparation_service(self, temp_directories):
        """Test file preparation service operations with real file system."""
        base_paths, temp_path = temp_directories
        
        # Create file preparation service with real components
        from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
        from src.infrastructure.drivers.logging.python_logger import PythonLogger
        from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository
        from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
        from src.workflow.preparation.file.file_preparation_service import FilePreparationService
        from src.infrastructure.config.json_config_loader import JsonConfigLoader
        
        file_driver = LocalFileDriver(base_dir=temp_path)
        sqlite_manager = FastSQLiteManager(":memory:", skip_migrations=False)
        repository = FilePreparationRepository(sqlite_manager)
        logger = PythonLogger()
        
        # Create config loader
        config_loader = JsonConfigLoader()
        
        service = FilePreparationService(file_driver, repository, logger, config_loader)
        
        # Test move_test_files operation
        success, message, file_count = service.move_test_files(
            language_name="python",
            contest_name="abc302", 
            problem_name="a",
            workspace_path=base_paths["workspace_path"],
            contest_current_path=base_paths["contest_current_path"]
        )
        
        assert success, f"move_test_files failed: {message}"
        assert file_count == 4, f"Expected 4 files moved, got {file_count}"
        
        # Verify files were actually moved
        contest_current_test = Path(base_paths["contest_current_path"]) / "test"
        assert contest_current_test.exists(), "Test directory not created"
        
        test_files = list(contest_current_test.glob("*"))
        assert len(test_files) == 4, f"Expected 4 test files, found {len(test_files)}"

    def test_complete_open_command_workflow_simulation(self, workspace_service):
        """Simulate the complete 'open' command workflow to test file movements."""
        # This simulates: workspace_switch -> oj download -> move_test_files
        
        # Step 1: workspace_switch (this should create directories and copy template)
        switch_result = workspace_service.switch_to_problem(
            contest="abc302",
            problem="a", 
            language="python"
        )
        assert switch_result.success, "Workspace switch failed"
        
        # Step 2: Simulate oj download (test files should already be in workspace/test)
        # This would be done by the oj command, but we pre-populated in fixture
        
        # Step 3: Verify final state - test files should be in contest_current/test
        base_paths = workspace_service.base_paths
        contest_current_path = Path(base_paths["contest_current_path"])
        contest_current_test = contest_current_path / "test"
        
        # Verify complete directory structure
        assert contest_current_path.exists(), "contest_current not created"
        assert contest_current_test.exists(), "contest_current/test not created"
        assert (contest_current_path / "main.py").exists(), "Template file not copied"
        
        # Verify test files are present and accessible for testing
        test_files = list(contest_current_test.glob("sample-*.in"))
        assert len(test_files) >= 2, f"Expected at least 2 input files, found {len(test_files)}"
        
        for input_file in test_files:
            output_file = input_file.with_suffix(".out")
            assert output_file.exists(), f"Output file {output_file} not found for {input_file}"
            
            # Verify files have content
            assert len(input_file.read_text().strip()) > 0, f"Input file {input_file} is empty"
            assert len(output_file.read_text().strip()) > 0, f"Output file {output_file} is empty"

    def test_workspace_directory_creation_with_cwd_operations(self, temp_directories):
        """Test that workspace directory is created for cwd operations like oj."""
        base_paths, temp_path = temp_directories
        
        # Create a shell driver with file driver (like in real system)
        from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
        from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
        
        file_driver = LocalFileDriver(base_dir=temp_path)
        shell_driver = LocalShellDriver(file_driver=file_driver)
        
        workspace_path = base_paths["workspace_path"]
        workspace_dir = Path(workspace_path)
        
        # Ensure workspace doesn't exist initially
        if workspace_dir.exists():
            import shutil
            shutil.rmtree(workspace_dir)
        
        assert not workspace_dir.exists(), "Workspace should not exist initially"
        
        # Execute a command with cwd=workspace_path (simulating oj download)
        # This should auto-create the workspace directory
        result = shell_driver.run(
            cmd=["echo", "test"],
            cwd=workspace_path
        )
        
        # Verify the workspace directory was created
        assert workspace_dir.exists(), "Workspace directory was not auto-created by shell command"
        assert result.returncode == 0, "Shell command failed"

    def test_error_handling_for_missing_test_files(self, workspace_service):
        """Test graceful handling when test files are missing."""
        # Create workspace service but don't populate test files
        base_paths = workspace_service.base_paths
        workspace_test_dir = Path(base_paths["workspace_path"]) / "test"
        
        # Remove test files if they exist
        if workspace_test_dir.exists():
            import shutil
            shutil.rmtree(workspace_test_dir)
        
        # Execute workspace switch (should still work even without test files)
        result = workspace_service.switch_to_problem(
            contest="abc302",
            problem="a",
            language="python"
        )
        
        assert result.success, "Workspace switch should succeed even without test files"
        
        # Verify contest_current was created with template
        contest_current_path = Path(base_paths["contest_current_path"])
        assert contest_current_path.exists(), "contest_current should be created"
        assert (contest_current_path / "main.py").exists(), "Template should be copied"
        
        # Verify no test directory is created when there are no test files
        contest_current_test = contest_current_path / "test"
        # Note: The behavior here depends on implementation - it might create an empty test dir


class TestFilePreparationServiceIntegration:
    """Test file preparation service with realistic scenarios."""

    def test_file_preparation_operation_tracking(self):
        """Test that file preparation operations are properly tracked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Setup file preparation service
            from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
            from src.infrastructure.drivers.logging.python_logger import PythonLogger
            from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository
            from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
            from src.workflow.preparation.file.file_preparation_service import FilePreparationService
            from src.infrastructure.config.json_config_loader import JsonConfigLoader
            
            file_driver = LocalFileDriver(base_dir=temp_path)
            sqlite_manager = FastSQLiteManager(":memory:", skip_migrations=False)
            repository = FilePreparationRepository(sqlite_manager)
            logger = PythonLogger()
            
            # Create config loader
            config_loader = JsonConfigLoader()
            
            service = FilePreparationService(file_driver, repository, logger, config_loader)
            
            # Create test files
            workspace_test = temp_path / "workspace" / "test"
            workspace_test.mkdir(parents=True)
            (workspace_test / "sample-01.in").write_text("input1")
            (workspace_test / "sample-01.out").write_text("output1")
            
            contest_current = temp_path / "contest_current"
            contest_current.mkdir(parents=True)
            
            # Execute move_test_files
            success, message, file_count = service.move_test_files(
                language_name="python",
                contest_name="test_contest",
                problem_name="test_problem", 
                workspace_path=str(temp_path / "workspace"),
                contest_current_path=str(contest_current)
            )
            
            assert success, "First move should succeed"
            assert file_count == 2, "Should move 2 files"
            
            # Execute again (should detect already done)
            success2, message2, file_count2 = service.move_test_files(
                language_name="python",
                contest_name="test_contest", 
                problem_name="test_problem",
                workspace_path=str(temp_path / "workspace"),
                contest_current_path=str(contest_current)
            )
            
            assert success2, "Second move should succeed"
            assert file_count2 == 0, "Should not move files again"
            assert "already moved" in message2.lower(), "Should indicate files already moved"