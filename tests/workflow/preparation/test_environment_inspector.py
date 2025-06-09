"""Tests for environment inspector module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.workflow.preparation.execution.environment_inspector import (
    EnvironmentInspector,
    ResourceRequirement,
    ResourceStatus,
    ResourceType,
)


class TestResourceType:
    """Test ResourceType enum."""

    def test_resource_type_values(self):
        """Test ResourceType enum values."""
        assert ResourceType.DOCKER_CONTAINER.value == "docker_container"
        assert ResourceType.DOCKER_IMAGE.value == "docker_image"
        assert ResourceType.DIRECTORY.value == "directory"
        assert ResourceType.FILE.value == "file"


class TestResourceRequirement:
    """Test ResourceRequirement dataclass."""

    def test_resource_requirement_creation(self):
        """Test ResourceRequirement creation."""
        requirement = ResourceRequirement(
            resource_type=ResourceType.DOCKER_CONTAINER,
            identifier="test_container",
            required_state="running",
            context_info={"key": "value"}
        )

        assert requirement.resource_type == ResourceType.DOCKER_CONTAINER
        assert requirement.identifier == "test_container"
        assert requirement.required_state == "running"
        assert requirement.context_info == {"key": "value"}

    def test_resource_requirement_creation_no_context(self):
        """Test ResourceRequirement creation without context."""
        requirement = ResourceRequirement(
            resource_type=ResourceType.DIRECTORY,
            identifier="/test/path",
            required_state="exists"
        )

        assert requirement.context_info is None


class TestResourceStatus:
    """Test ResourceStatus dataclass."""

    def test_resource_status_creation(self):
        """Test ResourceStatus creation."""
        status = ResourceStatus(
            resource_type=ResourceType.DOCKER_CONTAINER,
            identifier="test_container",
            current_state="stopped",
            exists=True,
            needs_preparation=True,
            preparation_actions=["start"]
        )

        assert status.resource_type == ResourceType.DOCKER_CONTAINER
        assert status.identifier == "test_container"
        assert status.current_state == "stopped"
        assert status.exists is True
        assert status.needs_preparation is True
        assert status.preparation_actions == ["start"]


class TestEnvironmentInspector:
    """Test EnvironmentInspector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_operations = MagicMock()
        self.mock_docker_driver = MagicMock()
        self.mock_file_driver = MagicMock()

        self.mock_operations.resolve.side_effect = lambda name: {
            "docker_driver": self.mock_docker_driver,
            "file_driver": self.mock_file_driver
        }.get(name)

        self.inspector = EnvironmentInspector(self.mock_operations)

    def test_init(self):
        """Test EnvironmentInspector initialization."""
        assert self.inspector.operations == self.mock_operations
        assert self.inspector._docker_driver == self.mock_docker_driver

    def test_extract_requirements_from_workflow_tasks_empty(self):
        """Test requirement extraction from empty workflow tasks."""
        workflow_tasks = []

        requirements = self.inspector.extract_requirements_from_workflow_tasks(workflow_tasks)

        assert isinstance(requirements, list)
        assert len(requirements) == 0

    def test_extract_requirements_from_workflow_tasks_with_docker(self):
        """Test requirement extraction with Docker tasks."""
        workflow_tasks = [{"request_type": "docker", "op_type": "exec"}]

        requirements = self.inspector.extract_requirements_from_workflow_tasks(workflow_tasks)

        assert isinstance(requirements, list)
        # Basic functionality test

    def test_inspect_docker_containers(self):
        """Test Docker container inspection."""
        required_containers = ["test_container"]

        status_map = self.inspector.inspect_docker_containers(required_containers)

        assert isinstance(status_map, dict)
        assert "test_container" in status_map
        assert isinstance(status_map["test_container"], ResourceStatus)

    def test_inspect_directories(self):
        """Test directory inspection."""
        required_directories = ["/test/dir1"]

        status_map = self.inspector.inspect_directories(required_directories)

        assert isinstance(status_map, dict)
        assert "/test/dir1" in status_map

    def test_extract_container_name_from_exec(self):
        """Test container name extraction from exec task."""
        exec_task = {"container_name": "test_container"}

        container_name = self.inspector._extract_container_name_from_exec(exec_task)

        assert container_name == "test_container"

    def test_extract_container_name_from_cp(self):
        """Test container name extraction from cp task."""
        cp_task = {"container_name": "test_container"}

        container_name = self.inspector._extract_container_name_from_cp(cp_task)

        assert container_name == "test_container"
