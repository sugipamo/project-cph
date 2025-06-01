"""
Integration test for main.py workflow execution with fitting
"""
import pytest
from unittest.mock import MagicMock, patch, call
import json

from src.main import main
from src.context.execution_context import ExecutionContext
from src.workflow_execution_service import WorkflowExecutionService, WorkflowExecutionResult
from src.operations.result.result import OperationResult


class TestMainWorkflowIntegration:
    """Test main.py integration with workflow execution and fitting"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock operations
        self.mock_operations = MagicMock()
        self.mock_docker_driver = MagicMock()
        self.mock_file_driver = MagicMock()
        self.mock_shell_driver = MagicMock()
        self.mock_python_driver = MagicMock()
        
        self.mock_operations.resolve.side_effect = lambda driver_type: {
            "docker_driver": self.mock_docker_driver,
            "file_driver": self.mock_file_driver,
            "shell_driver": self.mock_shell_driver,
            "python_driver": self.mock_python_driver
        }[driver_type]
        
        # Mock context with test workflow
        self.mock_context = MagicMock()
        self.mock_context.command_type = "test"
        self.mock_context.language = "python"
        self.mock_context.contest_name = "abc300"
        self.mock_context.problem_name = "a"
        self.mock_context.env_type = "local"
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python_abc300",
            "container_name": "cph_python_abc300",
            "oj_image_name": "ojtools_abc300",
            "oj_container_name": "cph_ojtools_abc300"
        }
        
        # Mock to_format_dict method
        self.mock_context.to_format_dict.return_value = {
            "command_type": "test",
            "language": "python",
            "contest_name": "abc300",
            "problem_name": "a",
            "env_type": "local",
            "workspace_path": "./workspace",
            "contest_current_path": "./contest_current"
        }
        
        # Mock env_json with workflow steps
        self.mock_context.env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [
                            {
                                "type": "mkdir",
                                "cmd": ["./workspace"]
                            },
                            {
                                "type": "copy",
                                "cmd": ["./contest_current/main.py", "./workspace/main.py"]
                            },
                            {
                                "type": "shell",
                                "cmd": ["echo", "Hello from test!"]
                            }
                        ]
                    }
                }
            }
        }
        
        # Mock dockerfile resolver
        mock_dockerfile_resolver = MagicMock()
        mock_dockerfile_resolver.dockerfile = None
        mock_dockerfile_resolver.oj_dockerfile = None
        self.mock_context.dockerfile_resolver = mock_dockerfile_resolver
    
    def test_main_executes_workflow_successfully(self, capsys):
        """Test that main() successfully executes a workflow"""
        # Mock successful results for all operations
        def create_success_result(stdout="", **kwargs):
            result = MagicMock()
            result.success = True
            result.stdout = stdout
            result.stderr = ""
            result.error = ""
            result.get_error_output.return_value = ""
            for k, v in kwargs.items():
                setattr(result, k, v)
            return result
        
        # Mock file driver to handle all file operations
        self.mock_file_driver.execute.return_value = create_success_result()
        self.mock_file_driver.exists.return_value = True
        self.mock_file_driver.mkdir.return_value = None
        
        # Mock shell driver to handle shell commands
        self.mock_shell_driver.execute.return_value = create_success_result(stdout="Hello from Python!")
        
        # Mock operations.resolve to return appropriate driver based on request type
        def resolve_driver(driver_type):
            return {
                "file_driver": self.mock_file_driver,
                "shell_driver": self.mock_shell_driver,
                "docker_driver": self.mock_docker_driver,
                "python_driver": self.mock_python_driver
            }[driver_type]
        
        self.mock_operations.resolve.side_effect = resolve_driver
        
        # Execute main
        result = main(self.mock_context, self.mock_operations)
        
        # Verify result
        assert result is not None
        assert result.success is True
        # May have additional steps from fitting
        assert len(result.results) >= 3  # At least mkdir, copy, shell
        assert all(r.success for r in result.results)
        
        # Check output
        captured = capsys.readouterr()
        assert "ワークフロー実行完了:" in captured.out
        assert "ステップ成功" in captured.out
        assert "Hello from test!" in captured.out
    
    def test_main_with_preparation_tasks(self, capsys):
        """Test main() with environment preparation needed"""
        # Mock successful results
        def create_success_result(stdout="", **kwargs):
            result = MagicMock()
            result.success = True
            result.stdout = stdout
            result.stderr = ""
            result.error = ""
            result.get_error_output.return_value = ""
            for k, v in kwargs.items():
                setattr(result, k, v)
            return result
        
        # Mock file operations
        self.mock_file_driver.execute.return_value = create_success_result()
        self.mock_file_driver.exists.return_value = False  # Directory doesn't exist
        self.mock_file_driver.mkdir.return_value = None
        self.mock_file_driver.copy.return_value = None
        
        # Mock shell operations
        self.mock_shell_driver.execute.return_value = create_success_result(stdout="Test passed!")
        
        with patch('src.workflow_execution_service.PreparationExecutor') as mock_prep_executor:
            # Mock preparation analysis
            mock_prep_instance = MagicMock()
            mock_prep_executor.return_value = mock_prep_instance
            
            # Mock that workspace needs to be created
            from src.env_integration.fitting.preparation_executor import PreparationTask
            from src.operations.file.file_request import FileRequest
            from src.operations.file.file_op_type import FileOpType
            
            prep_task = PreparationTask(
                task_id="mkdir_001",
                task_type="mkdir",
                request_object=FileRequest(FileOpType.MKDIR, "./workspace"),
                dependencies=[],
                description="Create directory: ./workspace",
                parallel_group="mkdir_preparation"
            )
            
            mock_prep_instance.analyze_and_prepare.return_value = (
                [prep_task],  # preparation tasks
                {"./workspace": MagicMock(needs_preparation=True)}  # statuses
            )
            
            mock_prep_instance.convert_to_workflow_requests.return_value = [
                FileRequest(FileOpType.MKDIR, "./workspace")
            ]
            
            # Execute main
            result = main(self.mock_context, self.mock_operations)
            
            # Verify result
            assert result is not None
            assert result.success is True
            
            # Check output mentions preparation
            captured = capsys.readouterr()
            assert "準備タスク実行: 1 件" in captured.out
            assert "✓ 準備タスク 1: 成功" in captured.out
    
    @patch('src.workflow_execution_service.WorkflowExecutionService')
    def test_main_handles_workflow_failure(self, mock_service_class, capsys):
        """Test main() handles workflow execution failure"""
        # Mock WorkflowExecutionService to return failure
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Create failed execution result
        from src.workflow_execution_service import WorkflowExecutionResult
        failed_result = WorkflowExecutionResult(
            success=False,
            results=[MagicMock(success=False, stdout="", get_error_output=lambda: "Permission denied")],
            preparation_results=[],
            errors=["Step 0 failed: Permission denied"],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = failed_result
        
        # Execute main and expect exception
        with pytest.raises(Exception) as exc_info:
            main(self.mock_context, self.mock_operations)
        
        assert "ワークフロー実行に失敗しました" in str(exc_info.value)
        
        # Check error output
        captured = capsys.readouterr()
        assert "エラー: Step 0 failed: Permission denied" in captured.out
    
    def test_main_handles_no_workflow_steps(self, capsys):
        """Test main() handles case with no workflow steps"""
        # Set empty workflow
        self.mock_context.env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": []
                    }
                }
            }
        }
        
        # Execute main and expect exception
        with pytest.raises(Exception) as exc_info:
            main(self.mock_context, self.mock_operations)
        
        assert "ワークフロー実行に失敗しました" in str(exc_info.value)
        
        # Check error output
        captured = capsys.readouterr()
        assert "No workflow steps found" in captured.out
    
    def test_workflow_execution_service_initialization(self):
        """Test WorkflowExecutionService is properly initialized"""
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        assert service.context == self.mock_context
        assert service.operations == self.mock_operations
        assert service.preparation_executor is not None
    
    def test_workflow_execution_service_get_steps(self):
        """Test WorkflowExecutionService correctly retrieves workflow steps"""
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        steps = service._get_workflow_steps()
        
        assert len(steps) == 3
        assert steps[0]["type"] == "mkdir"
        assert steps[1]["type"] == "copy"
        assert steps[2]["type"] == "shell"
    
    def test_main_with_warnings(self, capsys):
        """Test main() displays warnings from workflow execution"""
        # Create mock service with warnings
        with patch('src.workflow_execution_service.WorkflowExecutionService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock execution result with warnings
            mock_result = WorkflowExecutionResult(
                success=True,
                results=[MagicMock(success=True, output="")],
                preparation_results=[],
                errors=[],
                warnings=["Using deprecated feature", "Consider upgrading"]
            )
            mock_service.execute_workflow.return_value = mock_result
            
            # Execute main
            result = main(self.mock_context, self.mock_operations)
            
            # Check warnings are displayed
            captured = capsys.readouterr()
            assert "警告: Using deprecated feature" in captured.out
            assert "警告: Consider upgrading" in captured.out
            assert result.success is True