"""Integration test for the complete 'open' command workflow.

This test simulates the complete process:
1. Parse 'open abc302 a python local' command
2. Execute file_preparation (workspace_switch)
3. Execute oj download (mocked)
4. Execute file_preparation (move_test_files)
5. Verify final state has test files in contest_current/test

This is designed to catch the specific issue where test files don't appear
in contest_current after the open command.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from src.application.factories.unified_request_factory import UnifiedRequestFactory
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.workflow.step.core import generate_steps_from_json
from src.workflow.step.step import StepContext


class TestOpenCommandWorkflow:
    """Test the complete open command workflow end-to-end."""

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
            
            # Create template directory
            template_dir = temp_path / "contest_template" / "python"
            template_dir.mkdir(parents=True, exist_ok=True)
            (template_dir / "main.py").write_text("# Template file\nprint('Hello World')")
            
            yield base_paths, temp_path

    @pytest.fixture
    def mock_oj_download(self, temp_directories):
        """Mock oj download that creates test files in workspace."""
        base_paths, temp_path = temp_directories
        
        def simulate_oj_download(*args, **kwargs):
            """Simulate oj download creating test files."""
            workspace_test = Path(base_paths["workspace_path"]) / "test"
            workspace_test.mkdir(parents=True, exist_ok=True)
            
            # Create sample test files (simulating oj download result)
            (workspace_test / "sample-01.in").write_text("1 2\n")
            (workspace_test / "sample-01.out").write_text("3\n")
            (workspace_test / "sample-02.in").write_text("5 7\n") 
            (workspace_test / "sample-02.out").write_text("12\n")
            
            # Return successful result
            from src.domain.results.shell_result import ShellResult
            return ShellResult(stdout="Downloaded test cases", stderr="", returncode=0)
        
        return simulate_oj_download

    def test_complete_open_command_simulation(self, temp_directories, mock_oj_download):
        """Test complete open command workflow with real file operations."""
        base_paths, temp_path = temp_directories
        
        # Create the step context (simulating parsed command)
        context = StepContext(
            contest_name="abc302",
            problem_name="a", 
            language="python",
            env_type="local",
            command_type="open",
            workspace_path=base_paths["workspace_path"],
            contest_current_path=base_paths["contest_current_path"],
            contest_stock_path=base_paths["contest_stock_path"],
            contest_template_path=base_paths["contest_template_path"]
        )
        
        # Define the open command steps (from python env.json)
        open_steps = [
            {
                "type": "file_preparation",
                "allow_failure": False,
                "show_output": True,
                "operation_type": "workspace_switch",
                "context": {
                    "contest_name": "{contest_name}",
                    "problem_name": "{problem_name}",
                    "language": "{language_name}"
                }
            },
            {
                "type": "python",
                "allow_failure": True,
                "show_output": False,
                "cmd": [
                    "import webbrowser",
                    "webbrowser.open('https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}')"
                ]
            },
            {
                "type": "shell",
                "allow_failure": True,
                "show_output": False,
                "cmd": ["cursor", "{contest_current_path}/{source_file_name}"]
            },
            {
                "type": "oj",
                "allow_failure": True,
                "show_output": True,
                "cwd": "{workspace_path}",
                "cmd": ["oj", "download", "https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"]
            },
            {
                "type": "file_preparation",
                "allow_failure": True,
                "show_output": True,
                "operation_type": "move_test_files",
                "context": {
                    "contest_name": "{contest_name}",
                    "problem_name": "{problem_name}",
                    "language": "{language_name}"
                }
            }
        ]
        
        # Generate steps from JSON
        step_result = generate_steps_from_json(open_steps, context)
        assert len(step_result.errors) == 0, f"Step generation errors: {step_result.errors}"
        steps = step_result.steps
        
        # Create factory and environment manager
        factory = UnifiedRequestFactory()
        env_manager = EnvironmentManager("local")
        
        # Convert steps to requests
        requests = []
        for step in steps:
            request = factory.create_request_from_step(step, context, env_manager)
            if request is not None:
                requests.append(request)
        
        # Create drivers with real file operations
        from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
        from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
        from src.infrastructure.drivers.logging.python_logger import PythonLogger
        from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository
        from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
        from src.workflow.problem_workspace_service import ProblemWorkspaceService
        from src.infrastructure.drivers.workspace.workspace_driver import WorkspaceDriver
        
        file_driver = LocalFileDriver(base_dir=temp_path)
        shell_driver = LocalShellDriver(file_driver=file_driver)
        sqlite_manager = FastSQLiteManager(":memory:", skip_migrations=False)
        repository = FilePreparationRepository(sqlite_manager)
        logger = PythonLogger()
        
        workspace_service = ProblemWorkspaceService(
            file_driver=file_driver,
            repository=repository,
            logger=logger,
            base_paths=base_paths
        )
        workspace_driver = WorkspaceDriver(workspace_service)
        
        # Execute requests in order
        results = []
        for i, request in enumerate(requests):
            print(f"\\nExecuting step {i+1}: {type(request).__name__}")
            
            if hasattr(request, 'workspace_operation'):
                # File preparation request
                result = workspace_driver.execute(request)
                results.append(result)
                print(f"  Result: {result.success} - {result.content}")
                
            elif hasattr(request, 'cmd') and 'oj' in str(request.cmd):
                # Mock oj download
                with patch.object(shell_driver, 'run', side_effect=mock_oj_download):
                    result = request.execute(driver=shell_driver)
                    results.append(result)
                    print(f"  OJ Result: {result.success}")
                    
            elif hasattr(request, 'cmd'):
                # Other shell requests (cursor, etc.) - mock them
                with patch.object(shell_driver, 'run') as mock_run:
                    mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
                    result = request.execute(driver=shell_driver)
                    results.append(result)
                    print(f"  Shell Result: {result.success}")
                    
            elif hasattr(request, 'code_or_file'):
                # Python requests - mock them
                result = Mock()
                result.success = True
                result.content = "Python executed"
                results.append(result)
                print(f"  Python Result: {result.success}")
        
        # Verify final state
        contest_current_path = Path(base_paths["contest_current_path"])
        contest_current_test = contest_current_path / "test"
        
        print(f"\\nFinal verification:")
        print(f"contest_current exists: {contest_current_path.exists()}")
        print(f"contest_current/test exists: {contest_current_test.exists()}")
        
        if contest_current_test.exists():
            test_files = list(contest_current_test.glob("*"))
            print(f"Test files found: {[f.name for f in test_files]}")
        
        # Assertions
        assert contest_current_path.exists(), "contest_current directory was not created"
        assert contest_current_test.exists(), "test directory was not created in contest_current"
        
        # Check for test files
        input_files = list(contest_current_test.glob("sample-*.in"))
        output_files = list(contest_current_test.glob("sample-*.out"))
        
        assert len(input_files) >= 2, f"Expected at least 2 input files, found {len(input_files)}"
        assert len(output_files) >= 2, f"Expected at least 2 output files, found {len(output_files)}"
        
        # Verify file contents
        for input_file in input_files:
            output_file = input_file.with_suffix(".out")
            assert output_file.exists(), f"Output file {output_file} not found"
            assert len(input_file.read_text().strip()) > 0, f"Input file {input_file} is empty"
            assert len(output_file.read_text().strip()) > 0, f"Output file {output_file} is empty"

    def test_workspace_switch_only(self, temp_directories):
        """Test just the workspace_switch operation in isolation."""
        base_paths, temp_path = temp_directories
        
        # Create workspace service
        from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
        from src.infrastructure.drivers.logging.python_logger import PythonLogger
        from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository
        from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
        from src.workflow.problem_workspace_service import ProblemWorkspaceService
        
        file_driver = LocalFileDriver(base_dir=temp_path)
        sqlite_manager = FastSQLiteManager(":memory:", skip_migrations=False)
        repository = FilePreparationRepository(sqlite_manager)
        logger = PythonLogger()
        
        workspace_service = ProblemWorkspaceService(
            file_driver=file_driver,
            repository=repository,
            logger=logger,
            base_paths=base_paths
        )
        
        # Execute workspace switch
        result = workspace_service.switch_to_problem("abc302", "a", "python")
        
        assert result.success, f"Workspace switch failed: {result.message}"
        
        # Verify directories created
        contest_current_path = Path(base_paths["contest_current_path"])
        workspace_path = Path(base_paths["workspace_path"])
        
        assert contest_current_path.exists(), "contest_current was not created"
        assert workspace_path.exists(), "workspace was not created"
        assert (contest_current_path / "main.py").exists(), "Template was not copied"

    def test_move_test_files_only(self, temp_directories):
        """Test just the move_test_files operation in isolation."""
        base_paths, temp_path = temp_directories
        
        # Pre-create workspace with test files (simulating post-oj state)
        workspace_test = Path(base_paths["workspace_path"]) / "test"
        workspace_test.mkdir(parents=True)
        (workspace_test / "sample-01.in").write_text("1 2\n")
        (workspace_test / "sample-01.out").write_text("3\n")
        
        # Pre-create contest_current directory
        contest_current = Path(base_paths["contest_current_path"])
        contest_current.mkdir(parents=True)
        
        # Create file preparation service
        from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
        from src.infrastructure.drivers.logging.python_logger import PythonLogger
        from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository
        from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
        from src.workflow.preparation.file.file_preparation_service import FilePreparationService
        
        file_driver = LocalFileDriver(base_dir=temp_path)
        sqlite_manager = FastSQLiteManager(":memory:", skip_migrations=False)
        repository = FilePreparationRepository(sqlite_manager)
        logger = PythonLogger()
        
        service = FilePreparationService(file_driver, repository, logger)
        
        # Execute move_test_files
        success, message, file_count = service.move_test_files(
            language_name="python",
            contest_name="abc302",
            problem_name="a",
            workspace_path=base_paths["workspace_path"],
            contest_current_path=base_paths["contest_current_path"]
        )
        
        assert success, f"move_test_files failed: {message}"
        assert file_count == 2, f"Expected 2 files moved, got {file_count}"
        
        # Verify files moved
        contest_current_test = contest_current / "test"
        assert contest_current_test.exists(), "test directory not created in contest_current"
        assert (contest_current_test / "sample-01.in").exists(), "Input file not moved"
        assert (contest_current_test / "sample-01.out").exists(), "Output file not moved"


class TestOpenCommandDebugHelpers:
    """Helper tests for debugging the open command workflow."""

    def test_diagnose_file_preparation_chain(self):
        """Diagnostic test to understand the file preparation chain."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            print(f"\\nDiagnostic test using directory: {temp_path}")
            
            # Setup complete environment
            base_paths = {
                "contest_current_path": str(temp_path / "contest_current"),
                "contest_stock_path": str(temp_path / "contest_stock"),
                "contest_template_path": str(temp_path / "contest_template"),
                "workspace_path": str(temp_path / "workspace")
            }
            
            # Create template
            template_dir = temp_path / "contest_template" / "python"
            template_dir.mkdir(parents=True)
            (template_dir / "main.py").write_text("print('template')")
            
            # Create initial test files in workspace (simulating oj download)
            workspace_test = temp_path / "workspace" / "test"
            workspace_test.mkdir(parents=True)
            (workspace_test / "sample-01.in").write_text("input")
            (workspace_test / "sample-01.out").write_text("output")
            
            print(f"Initial state:")
            print(f"  Template exists: {template_dir.exists()}")
            print(f"  Workspace test exists: {workspace_test.exists()}")
            print(f"  Workspace test files: {list(workspace_test.glob('*'))}")
            
            # Create workspace service
            from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
            from src.infrastructure.drivers.logging.python_logger import PythonLogger
            from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository
            from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
            from src.workflow.problem_workspace_service import ProblemWorkspaceService
            
            file_driver = LocalFileDriver(base_dir=temp_path)
            sqlite_manager = FastSQLiteManager(":memory:", skip_migrations=False)
            repository = FilePreparationRepository(sqlite_manager)
            logger = PythonLogger()
            
            workspace_service = ProblemWorkspaceService(
                file_driver=file_driver,
                repository=repository,
                logger=logger,
                base_paths=base_paths
            )
            
            # Execute workspace switch
            print(f"\\nExecuting workspace_switch...")
            result = workspace_service.switch_to_problem("abc302", "a", "python")
            print(f"  Result: {result.success} - {result.message}")
            print(f"  Files moved: {result.files_moved}")
            
            # Check intermediate state
            contest_current = Path(base_paths["contest_current_path"])
            contest_current_test = contest_current / "test"
            workspace_test_after = Path(base_paths["workspace_path"]) / "test"
            
            print(f"\\nState after workspace_switch:")
            print(f"  contest_current exists: {contest_current.exists()}")
            print(f"  contest_current/test exists: {contest_current_test.exists()}")
            print(f"  workspace/test exists: {workspace_test_after.exists()}")
            
            if contest_current_test.exists():
                files = list(contest_current_test.glob("*"))
                print(f"  contest_current/test files: {[f.name for f in files]}")
            
            if workspace_test_after.exists():
                files = list(workspace_test_after.glob("*"))
                print(f"  workspace/test files: {[f.name for f in files]}")
            
            # This test is for diagnostic purposes - don't assert, just print results
            print(f"\\nDiagnostic complete. Check output above for file movement behavior.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])