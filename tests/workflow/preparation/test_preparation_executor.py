"""Tests for preparation executor module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.context.execution_context import ExecutionContext
from src.domain.requests.docker.docker_request import DockerOpType, DockerRequest
from src.domain.requests.file.file_request import FileOpType, FileRequest
from src.domain.requests.shell.shell_request import ShellRequest
from src.workflow.preparation.docker_state_manager_sqlite import DockerStateManagerSQLite
from src.workflow.preparation.environment_inspector import EnvironmentInspector, ResourceStatus, ResourceType
from src.workflow.preparation.preparation_executor import ContainerConfig, PreparationExecutor, PreparationTask


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

        with patch('src.workflow.preparation.preparation_executor.EnvironmentInspector'), \
             patch('src.workflow.preparation.preparation_executor.DockerStateManagerSQLite'), \
             patch('src.workflow.preparation.preparation_executor.PreparationErrorHandler'):
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
