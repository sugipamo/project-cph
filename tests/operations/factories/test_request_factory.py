"""Tests for request factory"""
import unittest
from typing import Any
from unittest.mock import Mock, patch

from src.operations.factories.request_factory import RequestFactory, create_request
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.docker.docker_request import DockerRequest
from src.operations.requests.file.file_request import FileRequest
from src.operations.requests.python.python_request import PythonRequest
from src.operations.requests.shell.shell_request import ShellRequest
from src.workflow.step.step import Step, StepType


class TestRequestFactory(unittest.TestCase):
    """Test cases for RequestFactory"""

    def setUp(self):
        """Set up test environment"""
        # Mock config manager
        self.mock_config_manager = Mock()

        # Mock context
        self.context = Mock()
        self.context.problem_name = "test_problem"

        # Mock environment manager
        self.env_manager = Mock()
        self.env_manager.get_workspace_root.return_value = "/workspace"

        # Create factory instance
        self.factory = RequestFactory(self.mock_config_manager)

    def test_init_with_config_manager(self):
        """Test factory initialization with config manager"""
        factory = RequestFactory(self.mock_config_manager)
        self.assertEqual(factory.config_manager, self.mock_config_manager)

    def test_init_without_config_manager(self):
        """Test factory initialization without config manager"""
        factory = RequestFactory()
        self.assertIsNone(factory.config_manager)

    def test_create_request_from_step_docker_build(self):
        """Test creating docker build request"""
        step = Step(type=StepType.DOCKER_BUILD, cmd=["build", "-t", "test:latest", "."])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, DockerRequest)

    def test_create_request_from_step_docker_run(self):
        """Test creating docker run request"""
        step = Step(type=StepType.DOCKER_RUN, cmd=["run", "--name", "test_container", "test:latest"])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, DockerRequest)
        self.assertEqual(result.container, "test_container")
        self.assertEqual(result.image, "test:latest")

    def test_create_request_from_step_docker_exec(self):
        """Test creating docker exec request"""
        step = Step(type=StepType.DOCKER_EXEC, cmd=["test_container", "echo", "hello"])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, DockerRequest)
        self.assertEqual(result.container, "test_container")
        self.assertEqual(result.command, ["echo", "hello"])

    def test_create_request_from_step_mkdir(self):
        """Test creating mkdir request"""
        step = Step(type=StepType.MKDIR, cmd=["test_dir"])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, FileRequest)
        self.assertEqual(result.path, "test_dir")

    def test_create_request_from_step_copy(self):
        """Test creating copy request"""
        step = Step(type=StepType.COPY, cmd=["source", "destination"])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, FileRequest)
        self.assertEqual(result.path, "source")
        self.assertEqual(result.dst_path, "destination")

    def test_create_request_from_step_move(self):
        """Test creating move request"""
        step = Step(type=StepType.MOVE, cmd=["source", "destination"])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, FileRequest)
        self.assertEqual(result.path, "source")
        self.assertEqual(result.dst_path, "destination")

    def test_create_request_from_step_remove(self):
        """Test creating remove request"""
        step = Step(type=StepType.REMOVE, cmd=["file_to_remove"])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, FileRequest)
        self.assertEqual(result.path, "file_to_remove")

    def test_create_request_from_step_run(self):
        """Test creating run (shell) request"""
        step = Step(type=StepType.RUN, cmd=["echo", "hello"], allow_failure=True)

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, ShellRequest)
        self.assertEqual(result.cmd, ["echo", "hello"])
        self.assertEqual(result.cwd, "/workspace")

    def test_create_request_from_step_python(self):
        """Test creating python request"""
        step = Step(type=StepType.PYTHON, cmd=["print('hello')", "x = 1"])

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsInstance(result, PythonRequest)
        self.assertEqual(result.code_or_file, ["print('hello')", "x = 1"])
        self.assertEqual(result.cwd, "/workspace")

    def test_create_request_from_step_unsupported_type(self):
        """Test creating request for unsupported step type"""
        # Create a mock step type that's not handled
        step = Mock()
        step.type = Mock()
        step.type.name = "UNKNOWN_TYPE"

        result = self.factory.create_request_from_step(step, self.context, self.env_manager)

        self.assertIsNone(result)


class TestCreateRequestFunction(unittest.TestCase):
    """Test cases for create_request function"""

    def setUp(self):
        """Set up test environment"""
        # Mock context with infrastructure
        self.context = Mock()
        self.context.infrastructure = Mock()

        # Mock environment manager
        self.mock_env_manager = Mock()
        self.context.infrastructure.resolve.return_value = self.mock_env_manager

    @patch('src.operations.factories.request_factory._factory_instance')
    def test_create_request_with_infrastructure(self, mock_factory):
        """Test create_request with context that has infrastructure"""
        step = Mock(spec=Step)
        mock_request = Mock(spec=OperationRequestFoundation)
        mock_factory.create_request_from_step.return_value = mock_request

        result = create_request(step, self.context)

        self.assertEqual(result, mock_request)
        mock_factory.create_request_from_step.assert_called_once_with(
            step, self.context, self.mock_env_manager
        )

    def test_create_request_without_infrastructure(self):
        """Test create_request with context that lacks infrastructure"""
        context = Mock()
        # Remove infrastructure attribute
        if hasattr(context, 'infrastructure'):
            delattr(context, 'infrastructure')

        step = Mock(spec=Step)

        result = create_request(step, context)

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
