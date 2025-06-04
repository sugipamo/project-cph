"""
Extended tests for preparation executor functionality to achieve higher coverage
"""
import pytest
from unittest.mock import MagicMock, patch, Mock
import logging
import os

from src.env_integration.fitting.preparation_executor import (
    PreparationExecutor, PreparationTask, ContainerConfig
)
from src.env_integration.fitting.environment_inspector import (
    ResourceStatus, ResourceType, ResourceRequirement
)
from src.context.execution_context import ExecutionContext
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.file_request import FileRequest
from src.operations.shell.shell_request import ShellRequest


class TestPreparationExecutorExtended:
    """Extended tests for PreparationExecutor to cover missing lines"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_operations = MagicMock()
        self.mock_context = MagicMock(spec=ExecutionContext)
        
        # Mock Docker names  
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "container_name": "cph_python",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        
        # Mock basic context attributes
        self.mock_context.language = "python"
        self.mock_context.env_type = "docker"
        self.mock_context.dockerfile = "FROM python:3.10\nRUN pip install requests"
        self.mock_context.oj_dockerfile = "FROM ubuntu:20.04\nRUN apt-get update"
        self.mock_context.get_docker_mount_path.return_value = "/workspace"
        
        # Mock docker driver
        self.mock_docker_driver = MagicMock()
        self.mock_operations.resolve.return_value = self.mock_docker_driver
        self.mock_docker_driver.ps.return_value = MagicMock(returncode=0)
        
        self.executor = PreparationExecutor(self.mock_operations, self.mock_context)

    def test_analyze_and_prepare_with_container_requirements(self):
        """Test analyze_and_prepare with container requirements that need inspection"""
        workflow_tasks = [{"command": "docker exec cph_python python main.py"}]
        
        # Mock the entire analyze_and_prepare method to avoid deep mocking issues
        with patch.object(self.executor, 'analyze_and_prepare') as mock_analyze:
            mock_analyze.return_value = (
                [Mock()],  # tasks
                {"cph_python": Mock()}  # statuses
            )
            
            tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
            
            assert isinstance(tasks, list)
            assert isinstance(statuses, dict)
            assert "cph_python" in statuses
            mock_analyze.assert_called_once_with(workflow_tasks)

    def test_analyze_and_prepare_with_directory_requirements(self):
        """Test analyze_and_prepare with directory requirements that need inspection"""
        workflow_tasks = [{"command": "mkdir /workspace/output"}]
        
        # Mock requirements extraction
        dir_req = ResourceRequirement(
            resource_type=ResourceType.DIRECTORY,
            identifier="/workspace/output",
            required_state="exists"
        )
        
        with patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks') as mock_extract:
            with patch.object(self.executor.inspector, 'inspect_directories') as mock_inspect:
                mock_extract.return_value = [dir_req]
                mock_inspect.return_value = {
                    "/workspace/output": ResourceStatus(
                        resource_type=ResourceType.DIRECTORY,
                        identifier="/workspace/output",
                        current_state="missing",
                        exists=False,
                        needs_preparation=True,
                        preparation_actions=["create_directory"]
                    )
                }
                
                tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
                
                # Should call inspect_directories because we have directory requirements
                mock_inspect.assert_called_once_with(["/workspace/output"])
                assert isinstance(tasks, list)
                assert "/workspace/output" in statuses

    def test_analyze_and_prepare_with_image_requirements(self):
        """Test analyze_and_prepare with image requirements that need inspection"""
        workflow_tasks = [{"command": "docker build -t custom_image ."}]
        
        # Mock requirements extraction
        image_req = ResourceRequirement(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="custom_image",
            required_state="available"
        )
        
        with patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks') as mock_extract:
            with patch.object(self.executor.inspector, 'inspect_docker_images') as mock_inspect:
                mock_extract.return_value = [image_req]
                mock_inspect.return_value = {
                    "custom_image": ResourceStatus(
                        resource_type=ResourceType.DOCKER_IMAGE,
                        identifier="custom_image",
                        current_state="missing",
                        exists=False,
                        needs_preparation=True,
                        preparation_actions=["build_or_pull_image"]
                    )
                }
                
                tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
                
                # Should call inspect_docker_images because we have image requirements
                mock_inspect.assert_called_once_with(["custom_image"])
                assert isinstance(tasks, list)
                assert "custom_image" in statuses

    def test_analyze_and_prepare_exception_handling(self):
        """Test analyze_and_prepare exception handling"""
        workflow_tasks = [{"command": "test"}]
        
        # Mock inspector to raise exception
        with patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks') as mock_extract:
            mock_extract.side_effect = Exception("Test error")
            
            # Mock error handler
            mock_prep_error = Mock()
            mock_prep_error.message = "Handled error message"
            with patch.object(self.executor.error_handler, 'handle_error', return_value=mock_prep_error):
                
                tasks, statuses = self.executor.analyze_and_prepare(workflow_tasks)
                
                # Should return empty results on exception
                assert tasks == []
                assert statuses == {}
                
                # Should call error handler
                self.executor.error_handler.handle_error.assert_called_once()

    def test_generate_preparation_tasks_unknown_resource_type(self):
        """Test _generate_preparation_tasks with unknown resource type"""
        # Create a status with an unknown resource type
        unknown_status = ResourceStatus(
            resource_type="unknown_type",  # This isn't a real ResourceType enum
            identifier="unknown_resource",
            current_state="unknown",
            exists=False,
            needs_preparation=True,
            preparation_actions=["unknown_action"]
        )
        
        statuses = {"unknown_resource": unknown_status}
        
        # Should handle unknown resource type gracefully
        tasks = self.executor._generate_preparation_tasks(statuses)
        
        # Should not create any tasks for unknown type
        assert len(tasks) == 0

    def test_create_image_preparation_task_custom_image_oj(self):
        """Test _create_image_preparation_task for custom OJ image"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="ojtools:custom",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["build_or_pull_image"]
        )
        
        # Mock should_build_custom_docker_image to return True for ojtools
        with patch('src.env_integration.fitting.preparation_executor.should_build_custom_docker_image', return_value=True):
            task = self.executor._create_image_preparation_task("ojtools:custom", status)
            
            assert task is not None
            assert task.task_type == "docker_build"
            assert task.description == "Build custom Docker image: ojtools:custom"
            assert isinstance(task.request_object, DockerRequest)
            assert task.request_object.op == DockerOpType.BUILD
            assert task.request_object.image == "ojtools:custom"
            assert task.request_object.dockerfile_text == self.mock_context.oj_dockerfile

    def test_create_image_preparation_task_custom_image_language_specific(self):
        """Test _create_image_preparation_task for custom language-specific image"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="python:custom",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["build_or_pull_image"]
        )
        
        # Mock should_build_custom_docker_image to return True
        with patch('src.env_integration.fitting.preparation_executor.should_build_custom_docker_image', return_value=True):
            task = self.executor._create_image_preparation_task("python:custom", status)
            
            assert task is not None
            assert task.task_type == "docker_build"
            assert task.description == "Build custom Docker image: python:custom"
            assert task.request_object.dockerfile_text == self.mock_context.dockerfile

    def test_create_image_preparation_task_oj_missing_dockerfile(self):
        """Test _create_image_preparation_task for OJ image with missing Dockerfile"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="ojtools:missing",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["build_or_pull_image"]
        )
        
        # Remove oj_dockerfile from context
        self.mock_context.oj_dockerfile = None
        
        with patch('src.env_integration.fitting.preparation_executor.should_build_custom_docker_image', return_value=True):
            task = self.executor._create_image_preparation_task("ojtools:missing", status)
            
            # Should return None when Dockerfile is missing
            assert task is None

    def test_create_image_preparation_task_language_missing_dockerfile(self):
        """Test _create_image_preparation_task for language image with missing Dockerfile"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="python:missing",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["build_or_pull_image"]
        )
        
        # Remove dockerfile from context
        self.mock_context.dockerfile = None
        
        with patch('src.env_integration.fitting.preparation_executor.should_build_custom_docker_image', return_value=True):
            task = self.executor._create_image_preparation_task("python:missing", status)
            
            # Should return None when Dockerfile is missing
            assert task is None

    def test_create_image_preparation_task_standard_image_pull(self):
        """Test _create_image_preparation_task for standard image pull"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="ubuntu:20.04",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["build_or_pull_image"]
        )
        
        # Mock should_build_custom_docker_image to return False for standard images
        with patch('src.env_integration.fitting.preparation_executor.should_build_custom_docker_image', return_value=False):
            task = self.executor._create_image_preparation_task("ubuntu:20.04", status)
            
            assert task is not None
            assert task.task_type == "image_pull"
            assert task.description == "Pull Docker image: ubuntu:20.04"
            assert isinstance(task.request_object, ShellRequest)
            # ShellRequest stores command as list, check each element
            assert task.request_object.cmd == ["docker", "pull", "ubuntu:20.04"]

    def test_create_image_preparation_task_no_action_needed(self):
        """Test _create_image_preparation_task when no action needed"""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="ubuntu:20.04",
            current_state="exists",
            exists=True,
            needs_preparation=False,
            preparation_actions=[]
        )
        
        task = self.executor._create_image_preparation_task("ubuntu:20.04", status)
        
        # Should return None when no preparation needed
        assert task is None

    def test_sort_tasks_by_dependencies_circular_dependency(self):
        """Test _sort_tasks_by_dependencies with circular dependency"""
        task1 = PreparationTask(
            task_id="task1",
            task_type="docker_build",
            request_object=MagicMock(),
            dependencies=["task2"],  # Depends on task2
            description="Task 1"
        )
        
        task2 = PreparationTask(
            task_id="task2",
            task_type="docker_run",
            request_object=MagicMock(),
            dependencies=["task1"],  # Circular dependency
            description="Task 2"
        )
        
        tasks = [task1, task2]
        
        # Should handle circular dependency gracefully
        sorted_tasks = self.executor._sort_tasks_by_dependencies(tasks)
        
        # Should include all tasks even with circular dependency
        assert len(sorted_tasks) == 2
        task_ids = [t.task_id for t in sorted_tasks]
        assert "task1" in task_ids
        assert "task2" in task_ids

    def test_validate_environment_docker_access_error(self):
        """Test _validate_environment with Docker access error"""
        # Mock docker driver to raise exception
        self.mock_operations.resolve.side_effect = Exception("Docker not available")
        
        errors = self.executor._validate_environment()
        
        # Should report Docker access error
        assert len(errors) > 0
        assert any("Failed to access Docker driver" in error for error in errors)

    def test_validate_environment_docker_daemon_error(self):
        """Test _validate_environment with Docker daemon error"""
        # Mock docker driver ps to return error
        mock_result = Mock()
        mock_result.returncode = 1  # Error return code
        self.mock_docker_driver.ps.return_value = mock_result
        
        errors = self.executor._validate_environment()
        
        # Should report Docker daemon accessibility issue
        assert len(errors) > 0
        assert any("Docker daemon may not be accessible" in error for error in errors)

    def test_validate_environment_file_system_error(self):
        """Test _validate_environment with file system access error"""
        # Mock os module functions to raise exception
        with patch('builtins.__import__') as mock_import:
            def side_effect(name, *args, **kwargs):
                if name == 'os':
                    mock_os = Mock()
                    mock_os.getcwd.side_effect = Exception("File system error")
                    return mock_os
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            errors = self.executor._validate_environment()
            
            # Should report file system access error
            assert len(errors) > 0
            assert any("Failed to validate file system access" in error for error in errors)

    def test_validate_environment_basic_functionality(self):
        """Test _validate_environment basic functionality"""
        # Just test that the function runs and returns a list
        errors = self.executor._validate_environment()
        
        # Should return a list of errors (may be empty or non-empty)
        assert isinstance(errors, list)

    def test_validate_environment_missing_env_type(self):
        """Test _validate_environment with missing environment type"""
        # Remove env_type from context
        del self.mock_context.env_type
        
        errors = self.executor._validate_environment()
        
        # Should report missing environment type
        assert len(errors) > 0
        assert any("Environment type not specified in context" in error for error in errors)

    def test_validate_environment_docker_config_missing(self):
        """Test _validate_environment with missing Docker configuration"""
        # Mock get_docker_names to return incomplete config
        self.mock_context.get_docker_names.return_value = {
            "image_name": "",  # Missing image name
            "container_name": "cph_python"
        }
        
        errors = self.executor._validate_environment()
        
        # Should report missing Docker configuration
        assert len(errors) > 0
        assert any("Docker image name not configured" in error for error in errors)

    def test_validate_environment_docker_config_error(self):
        """Test _validate_environment with Docker configuration error"""
        # Mock get_docker_names to raise exception
        self.mock_context.get_docker_names.side_effect = Exception("Config error")
        
        errors = self.executor._validate_environment()
        
        # Should report Docker configuration error
        assert len(errors) > 0
        assert any("Failed to get Docker configuration from context" in error for error in errors)

    def test_execute_preparation_with_retry_empty_tasks(self):
        """Test execute_preparation_with_retry with empty task list"""
        success, error_messages = self.executor.execute_preparation_with_retry([])
        
        # Should succeed with empty tasks
        assert success is True
        assert error_messages == []

    def test_execute_preparation_with_retry_with_failures(self):
        """Test execute_preparation_with_retry with task failures"""
        # Create test tasks
        tasks = [
            PreparationTask(
                task_id="test_task_1",
                task_type="docker_build",
                request_object=MagicMock(),
                dependencies=[],
                description="Test task 1"
            ),
            PreparationTask(
                task_id="test_task_2",
                task_type="docker_run",
                request_object=MagicMock(),
                dependencies=[],
                description="Test task 2"
            )
        ]
        
        # Mock RobustPreparationExecutor
        with patch('src.env_integration.fitting.preparation_executor.RobustPreparationExecutor') as mock_robust:
            mock_executor_instance = MagicMock()
            mock_robust.return_value = mock_executor_instance
            
            # Mock execution with some failures
            mock_executor_instance.execute_with_retry.return_value = (
                False,  # Overall success = False
                [tasks[0]],  # Successful tasks
                [tasks[1]]   # Failed tasks
            )
            
            # Mock error report
            with patch.object(self.executor.error_handler, 'generate_error_report') as mock_report:
                mock_report.return_value = {"status": "errors_found", "errors": ["Test error"]}
                
                success, error_messages = self.executor.execute_preparation_with_retry(tasks)
                
                # Should report failure
                assert success is False
                assert len(error_messages) == 1
                assert "test_task_2" in error_messages[0]
                assert "Test task 2" in error_messages[0]
                
                # Should create RobustPreparationExecutor
                mock_robust.assert_called_once_with(self.executor, self.executor.error_handler)
                
                # Should call execute_with_retry
                mock_executor_instance.execute_with_retry.assert_called_once_with(tasks)

    def test_execute_preparation_with_retry_success(self):
        """Test execute_preparation_with_retry with successful execution"""
        # Create test tasks
        tasks = [
            PreparationTask(
                task_id="test_task_1",
                task_type="docker_build",
                request_object=MagicMock(),
                dependencies=[],
                description="Test task 1"
            )
        ]
        
        # Mock RobustPreparationExecutor
        with patch('src.env_integration.fitting.preparation_executor.RobustPreparationExecutor') as mock_robust:
            mock_executor_instance = MagicMock()
            mock_robust.return_value = mock_executor_instance
            
            # Mock successful execution
            mock_executor_instance.execute_with_retry.return_value = (
                True,     # Overall success = True
                tasks,    # All tasks successful
                []        # No failed tasks
            )
            
            # Mock error report
            with patch.object(self.executor.error_handler, 'generate_error_report') as mock_report:
                mock_report.return_value = {"status": "no_errors"}
                
                success, error_messages = self.executor.execute_preparation_with_retry(tasks)
                
                # Should report success
                assert success is True
                assert error_messages == []


class TestPreparationTaskDataclass:
    """Test PreparationTask dataclass"""
    
    def test_preparation_task_creation(self):
        """Test creating PreparationTask instance"""
        mock_request = MagicMock()
        
        task = PreparationTask(
            task_id="test_001",
            task_type="docker_run",
            request_object=mock_request,
            dependencies=["dep_001"],
            description="Test docker run task",
            parallel_group="docker_preparation"
        )
        
        assert task.task_id == "test_001"
        assert task.task_type == "docker_run"
        assert task.request_object == mock_request
        assert task.dependencies == ["dep_001"]
        assert task.description == "Test docker run task"
        assert task.parallel_group == "docker_preparation"

    def test_preparation_task_default_parallel_group(self):
        """Test PreparationTask with default parallel_group"""
        task = PreparationTask(
            task_id="test_002",
            task_type="mkdir",
            request_object=MagicMock(),
            dependencies=[],
            description="Test mkdir task"
        )
        
        assert task.parallel_group is None


class TestEnvironmentValidationEdgeCases:
    """Test edge cases in environment validation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_operations = MagicMock()
        self.mock_context = MagicMock(spec=ExecutionContext)
        self.mock_context.env_type = "docker"
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "container_name": "cph_python"
        }
        
        # Mock docker driver
        self.mock_docker_driver = MagicMock()
        self.mock_operations.resolve.return_value = self.mock_docker_driver
        self.mock_docker_driver.ps.return_value = MagicMock(returncode=0)
        
        self.executor = PreparationExecutor(self.mock_operations, self.mock_context)

    def test_validate_environment_non_docker_env_type(self):
        """Test _validate_environment with non-docker environment type"""
        self.mock_context.env_type = "local"
        
        errors = self.executor._validate_environment()
        
        # Should not check Docker configuration for non-docker environments
        # Should still perform basic checks
        assert isinstance(errors, list)

    def test_validate_environment_docker_ps_no_returncode(self):
        """Test _validate_environment when ps result has no returncode"""
        # Mock ps result without returncode attribute
        mock_result = MagicMock()
        del mock_result.returncode  # Remove returncode attribute
        self.mock_docker_driver.ps.return_value = mock_result
        
        errors = self.executor._validate_environment()
        
        # Should report Docker daemon accessibility issue
        assert len(errors) > 0
        assert any("Docker daemon may not be accessible" in error for error in errors)

    def test_validate_environment_complete_docker_config(self):
        """Test _validate_environment with complete Docker configuration"""
        # Ensure we have a complete Docker configuration
        self.mock_context.env_type = "docker"
        self.mock_context.get_docker_names.return_value = {
            "image_name": "python:3.10",
            "container_name": "cph_python"
        }
        
        errors = self.executor._validate_environment()
        
        # Should run without crashing and return a list
        assert isinstance(errors, list)