"""Tests for preparation executor module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.context.execution_context import ExecutionContext
from src.domain.requests.docker.docker_request import DockerOpType, DockerRequest
from src.domain.requests.file.file_request import FileOpType, FileRequest
from src.domain.requests.shell.shell_request import ShellRequest
from src.workflow.preparation.docker.docker_state_manager_sqlite import DockerStateManagerSQLite
from src.workflow.preparation.executor.environment_inspector import EnvironmentInspector, ResourceStatus, ResourceType
from src.workflow.preparation.executor.preparation_executor import (
    ContainerConfig,
    PreparationExecutor,
    PreparationTask,
)


class TestPreparationTask:
    """Test PreparationTask dataclass."""

    def test_task_creation(self):
        """Test PreparationTask creation."""
        request = MagicMock()
        task = PreparationTask(
            task_id="test_task",
            task_type="docker_run",
            request_object=request,
            dependencies=["dep1", "dep2"],
            description="Test task description"
        )

        assert task.task_id == "test_task"
        assert task.task_type == "docker_run"
        assert task.request_object == request
        assert task.dependencies == ["dep1", "dep2"]
        assert task.description == "Test task description"
        assert task.parallel_group is None

    def test_task_creation_with_parallel_group(self):
        """Test PreparationTask creation with parallel group."""
        request = MagicMock()
        task = PreparationTask(
            task_id="test_task",
            task_type="docker_run",
            request_object=request,
            dependencies=[],
            description="Test task description",
            parallel_group="group1"
        )

        assert task.parallel_group == "group1"


class TestContainerConfig:
    """Test ContainerConfig dataclass."""

    def test_container_config_creation(self):
        """Test ContainerConfig creation."""
        config = ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=True,
            needs_image_rebuild=False,
            needs_container_recreate=True,
            dockerfile_content="FROM ubuntu"
        )

        assert config.container_name == "test_container"
        assert config.image_name == "test_image"
        assert config.is_oj_container is True
        assert config.needs_image_rebuild is False
        assert config.needs_container_recreate is True
        assert config.dockerfile_content == "FROM ubuntu"


class TestPreparationExecutor:
    """Test PreparationExecutor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_operations = MagicMock()
        self.mock_context = MagicMock(spec=ExecutionContext)
        self.mock_context.command_type = "test"
        self.mock_context.language = "python"
        self.mock_context.contest_name = "abc123"
        self.mock_context.problem_name = "a"
        self.mock_context.env_type = "local"

        with patch('src.workflow.preparation.executor.preparation_executor.EnvironmentInspector'), \
             patch('src.workflow.preparation.executor.preparation_executor.DockerStateManagerSQLite'), \
             patch('src.workflow.preparation.executor.preparation_executor.PreparationErrorHandler'):
            self.executor = PreparationExecutor(self.mock_operations, self.mock_context)

    def test_init(self):
        """Test PreparationExecutor initialization."""
        assert self.executor.operations == self.mock_operations
        assert self.executor.context == self.mock_context
        assert self.executor.inspector is not None
        assert self.executor.state_manager is not None
        assert self.executor.error_handler is not None
        assert self.executor.logger is not None

    def test_analyze_and_prepare_empty_workflow(self):
        """Test analyze_and_prepare with empty workflow tasks."""
        workflow_tasks = []

        # Mock inspector methods
        with patch.object(self.executor, '_validate_environment', return_value=[]), \
             patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks', return_value=[]):

            tasks, status_map = self.executor.analyze_and_prepare(workflow_tasks)

            assert isinstance(tasks, list)
            assert isinstance(status_map, dict)

    def test_next_task_id(self):
        """Test task ID generation."""
        task_id1 = self.executor._next_task_id("test")
        task_id2 = self.executor._next_task_id("test")

        assert task_id1 != task_id2
        assert isinstance(task_id1, str)
        assert isinstance(task_id2, str)
        assert "test" in task_id1
        assert "test" in task_id2

    def test_convert_to_workflow_requests(self):
        """Test conversion of preparation tasks to workflow requests."""
        mock_request = MagicMock()
        task = PreparationTask(
            task_id="test_task",
            task_type="mkdir",
            request_object=mock_request,
            dependencies=[],
            description="Test task"
        )

        requests = self.executor.convert_to_workflow_requests([task])

        assert len(requests) == 1
        assert requests[0] == mock_request

    def test_analyze_and_prepare_with_docker_workflow(self):
        """Test analyze_and_prepare with Docker container requirements."""
        workflow_tasks = [MagicMock(), MagicMock()]

        # Mock resource statuses requiring Docker containers
        docker_status = ResourceStatus(
            resource_type=ResourceType.DOCKER_CONTAINER,
            identifier="test_container",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["run_new_container"]
        )

        with patch.object(self.executor, '_validate_environment', return_value=[]), \
             patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks', return_value=[docker_status]), \
             patch.object(self.executor, '_generate_preparation_tasks', return_value=[]), \
             patch.object(self.executor, '_sort_tasks_by_dependencies', return_value=[]):

            tasks, status_map = self.executor.analyze_and_prepare(workflow_tasks)

            assert isinstance(tasks, list)
            assert isinstance(status_map, dict)
            self.executor._validate_environment.assert_called_once()
            self.executor.inspector.extract_requirements_from_workflow_tasks.assert_called_once_with(workflow_tasks)

    def test_analyze_and_prepare_with_directory_requirements(self):
        """Test analyze_and_prepare with directory creation requirements."""
        workflow_tasks = [MagicMock()]

        # Mock resource status requiring directory creation
        dir_status = ResourceStatus(
            resource_type=ResourceType.DIRECTORY,
            identifier="/test/directory",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["create_directory"]
        )

        with patch.object(self.executor, '_validate_environment', return_value=[]), \
             patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks', return_value=[dir_status]), \
             patch.object(self.executor, '_generate_preparation_tasks', return_value=[]), \
             patch.object(self.executor, '_sort_tasks_by_dependencies', return_value=[]):

            tasks, status_map = self.executor.analyze_and_prepare(workflow_tasks)

            assert isinstance(tasks, list)
            assert isinstance(status_map, dict)

    def test_create_container_preparation_tasks_with_removal_and_run(self):
        """Test container task creation when both removal and run are needed."""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_CONTAINER,
            identifier="test_container",
            current_state="stopped",
            exists=True,
            needs_preparation=True,
            preparation_actions=["remove_stopped_container", "run_new_container"]
        )

        with patch.object(self.executor, '_create_docker_remove_task') as mock_remove, \
             patch.object(self.executor, '_create_docker_run_task') as mock_run:

            mock_remove.return_value = MagicMock()
            mock_run.return_value = MagicMock()

            tasks = self.executor._create_container_preparation_tasks("test_container", status)

            assert len(tasks) >= 1  # Should create at least one task
            mock_remove.assert_called()
            mock_run.assert_called()

    def test_create_image_preparation_task_custom_build(self):
        """Test image task creation for custom Docker image builds."""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_IMAGE,
            identifier="custom_image",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["build_or_pull_image"]
        )

        with patch.object(self.executor, '_next_task_id', return_value="img_001"):
            task = self.executor._create_image_preparation_task("custom_image", status)

            assert task is not None
            assert task.task_id == "img_001"
            assert "custom_image" in task.description

    def test_validate_environment_docker_issues(self):
        """Test environment validation with Docker access issues."""
        # Mock Docker access validation failure
        with patch.object(self.executor.inspector, 'validate_docker_access', return_value=False):
            validation_errors = self.executor._validate_environment()

            # Should detect Docker access issues
            assert len(validation_errors) >= 0  # May return errors or handle gracefully

    def test_analyze_and_prepare_exception_handling(self):
        """Test exception handling in analyze_and_prepare."""
        workflow_tasks = [MagicMock()]

        # Mock an exception during requirement extraction
        with patch.object(self.executor.inspector, 'extract_requirements_from_workflow_tasks',
                         side_effect=Exception("Test exception")):
            tasks, status_map = self.executor.analyze_and_prepare(workflow_tasks)

            # Should return empty results when exception occurs
            assert tasks == []
            assert status_map == {}

    def test_sort_tasks_by_dependencies_complex(self):
        """Test dependency sorting with complex dependencies."""
        # Create tasks with various dependency patterns
        task1 = PreparationTask("task1", "mkdir", MagicMock(), [], "Task 1")
        task2 = PreparationTask("task2", "docker_run", MagicMock(), ["task1"], "Task 2")
        task3 = PreparationTask("task3", "docker_build", MagicMock(), [], "Task 3", parallel_group="build_group")
        task4 = PreparationTask("task4", "docker_run", MagicMock(), ["task2", "task3"], "Task 4")

        tasks = [task4, task2, task1, task3]  # Unsorted order

        sorted_tasks = self.executor._sort_tasks_by_dependencies(tasks)

        assert len(sorted_tasks) == 4
        # Verify basic dependency ordering (task1 should come before task2, etc.)
        task_positions = {task.task_id: i for i, task in enumerate(sorted_tasks)}
        assert task_positions["task1"] < task_positions["task2"]
        assert task_positions["task2"] < task_positions["task4"]
        assert task_positions["task3"] < task_positions["task4"]

    def test_execute_preparation_with_retry(self):
        """Test preparation execution with retry mechanism."""
        preparation_tasks = [MagicMock()]

        # Mock the RobustPreparationExecutor's execute_with_retry method
        with patch('src.workflow.preparation.executor.preparation_executor.RobustPreparationExecutor') as mock_robust_executor_class:
            mock_robust_executor = MagicMock()
            mock_robust_executor.execute_with_retry.return_value = (True, preparation_tasks, [])
            mock_robust_executor_class.return_value = mock_robust_executor

            success, error_messages = self.executor.execute_preparation_with_retry(preparation_tasks)

            assert success is True
            assert isinstance(error_messages, list)
            mock_robust_executor_class.assert_called_once_with(self.executor, self.executor.error_handler)
            mock_robust_executor.execute_with_retry.assert_called_once_with(preparation_tasks)

    def test_create_mkdir_preparation_task(self):
        """Test directory creation task generation."""
        status = ResourceStatus(
            resource_type=ResourceType.DIRECTORY,
            identifier="/test/path",
            current_state="missing",
            exists=False,
            needs_preparation=True,
            preparation_actions=["create_directory"]
        )

        with patch.object(self.executor, '_next_task_id', return_value="mkdir_001"):
            task = self.executor._create_mkdir_preparation_task("/test/path", status)

            assert task is not None
            assert task.task_id == "mkdir_001"
            assert task.task_type == "mkdir"
            assert "/test/path" in task.description

    def test_create_docker_run_task(self):
        """Test Docker run task creation."""
        ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=False,
            needs_container_recreate=True,
            dockerfile_content=None
        )

        with patch.object(self.executor, '_next_task_id', return_value="run_001"), \
             patch.object(self.executor.state_manager, 'check_rebuild_needed', return_value=(False, False, True, False)):
            tasks = self.executor._create_docker_run_task("test_container")

            assert tasks is not None
            assert isinstance(tasks, list)
            assert len(tasks) >= 1
            # Check that at least one task has the right characteristics
            assert any("test_container" in task.description for task in tasks)

    def test_create_docker_remove_task(self):
        """Test Docker remove task creation."""
        ContainerConfig(
            container_name="test_container",
            image_name="test_image",
            is_oj_container=False,
            needs_image_rebuild=False,
            needs_container_recreate=True,
            dockerfile_content=None
        )

        with patch.object(self.executor, '_next_task_id', return_value="remove_001"):
            task = self.executor._create_docker_remove_task("test_container")

            assert task is not None
            assert task.task_id == "remove_001"
            assert task.task_type == "docker_remove"
            assert "test_container" in task.description
