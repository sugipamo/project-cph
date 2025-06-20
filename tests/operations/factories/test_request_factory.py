"""Tests for request factory"""
from unittest.mock import Mock

import pytest

from src.operations.factories.request_factory import RequestFactory, create_request
from src.operations.requests.docker.docker_request import DockerRequest
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest
from src.operations.requests.python.python_request import PythonRequest
from src.operations.requests.shell.shell_request import ShellRequest
from src.workflow.step.step import Step, StepType


class TestRequestFactory:
    """Test RequestFactory class"""

    @pytest.fixture
    def factory(self):
        """Create RequestFactory instance"""
        return RequestFactory()

    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        context = Mock()
        context.problem_name = "test_problem"
        return context

    @pytest.fixture
    def mock_env_manager(self):
        """Create mock environment manager"""
        env_manager = Mock()
        env_manager.get_workspace_root.return_value = "/workspace"
        return env_manager

    def test_create_request_from_step_unsupported_type(self, factory, mock_context, mock_env_manager):
        """Test creating request from step with unsupported type"""
        # Create a step with unsupported type (using OJ as example)
        step = Step(type=StepType.OJ, cmd=["test"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert result is None

    def test_create_docker_build_request(self, factory, mock_context, mock_env_manager):
        """Test creating Docker build request"""
        step = Step(type=StepType.DOCKER_BUILD, cmd=["docker", "build", "-t", "test:latest", "."])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.op == "build"
        assert result.context_path == "/workspace"
        assert result.tag == "test:latest"
        assert result.debug_tag == "docker_build_test_problem"

    def test_create_docker_build_request_no_tag(self, factory, mock_context, mock_env_manager):
        """Test creating Docker build request without tag"""
        step = Step(type=StepType.DOCKER_BUILD, cmd=["docker", "build", "."])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.op == "build"
        assert result.tag is None

    def test_create_docker_run_request(self, factory, mock_context, mock_env_manager):
        """Test creating Docker run request"""
        step = Step(type=StepType.DOCKER_RUN, cmd=["docker", "run", "--name", "test-container", "test:latest"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.op == "run"
        assert result.image == "test:latest"
        assert result.container == "test-container"
        assert result.workspace_mount == "/workspace"
        assert result.debug_tag == "docker_run_test_problem"

    def test_create_docker_run_request_no_name(self, factory, mock_context, mock_env_manager):
        """Test creating Docker run request without container name"""
        step = Step(type=StepType.DOCKER_RUN, cmd=["docker", "run", "test:latest"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container is None
        assert result.image == "test:latest"

    def test_create_docker_exec_request(self, factory, mock_context, mock_env_manager):
        """Test creating Docker exec request"""
        step = Step(type=StepType.DOCKER_EXEC, cmd=["test-container", "ls", "-la"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.op == "exec"
        assert result.container == "test-container"
        assert result.cmd == ["ls", "-la"]
        assert result.debug_tag == "docker_exec_test_problem"

    def test_create_docker_exec_request_empty_cmd(self, factory, mock_context, mock_env_manager):
        """Test creating Docker exec request with empty command"""
        step = Step(type=StepType.DOCKER_EXEC, cmd=[])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container is None
        assert result.cmd == []

    def test_create_docker_commit_request(self, factory, mock_context, mock_env_manager):
        """Test creating Docker commit request"""
        step = Step(type=StepType.DOCKER_COMMIT, cmd=["test-container", "test:committed"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.op == "commit"
        assert result.container == "test-container"
        assert result.image == "test:committed"
        assert result.debug_tag == "docker_commit_test_problem"

    def test_create_docker_rm_request(self, factory, mock_context, mock_env_manager):
        """Test creating Docker rm request"""
        step = Step(type=StepType.DOCKER_RM, cmd=["test-container"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.op == "rm"
        assert result.container == "test-container"
        assert result.debug_tag == "docker_rm_test_problem"

    def test_create_docker_rmi_request(self, factory, mock_context, mock_env_manager):
        """Test creating Docker rmi request"""
        step = Step(type=StepType.DOCKER_RMI, cmd=["test:latest"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.op == "rmi"
        assert result.image == "test:latest"
        assert result.debug_tag == "docker_rmi_test_problem"

    def test_create_mkdir_request(self, factory, mock_context, mock_env_manager):
        """Test creating mkdir request"""
        step = Step(type=StepType.MKDIR, cmd=["test_dir"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.MKDIR
        assert result.path == "test_dir"
        assert result.debug_tag == "mkdir_test_problem"

    def test_create_touch_request(self, factory, mock_context, mock_env_manager):
        """Test creating touch request"""
        step = Step(type=StepType.TOUCH, cmd=["test_file.txt"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.TOUCH
        assert result.path == "test_file.txt"
        assert result.debug_tag == "touch_test_problem"

    def test_create_copy_request(self, factory, mock_context, mock_env_manager):
        """Test creating copy request"""
        step = Step(type=StepType.COPY, cmd=["source.txt", "dest.txt"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.COPY
        assert result.path == "source.txt"
        assert result.dst_path == "dest.txt"
        assert result.debug_tag == "copy_test_problem"

    def test_create_move_request(self, factory, mock_context, mock_env_manager):
        """Test creating move request"""
        step = Step(type=StepType.MOVE, cmd=["source.txt", "dest.txt"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.MOVE
        assert result.path == "source.txt"
        assert result.dst_path == "dest.txt"
        assert result.debug_tag == "move_test_problem"

    def test_create_remove_request(self, factory, mock_context, mock_env_manager):
        """Test creating remove request"""
        step = Step(type=StepType.REMOVE, cmd=["test_file.txt"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.REMOVE
        assert result.path == "test_file.txt"
        assert result.debug_tag == "remove_test_problem"

    def test_create_rmtree_request(self, factory, mock_context, mock_env_manager):
        """Test creating rmtree request"""
        step = Step(type=StepType.RMTREE, cmd=["test_dir"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.RMTREE
        assert result.path == "test_dir"
        assert result.debug_tag == "rmtree_test_problem"

    def test_create_chmod_request(self, factory, mock_context, mock_env_manager):
        """Test creating chmod request"""
        step = Step(type=StepType.CHMOD, cmd=["755", "test_file.txt"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.CHMOD
        assert result.path == "test_file.txt"
        assert result.debug_tag == "chmod_test_problem"

    def test_create_run_request(self, factory, mock_context, mock_env_manager):
        """Test creating run (shell) request"""
        step = Step(type=StepType.RUN, cmd=["echo", "hello"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, ShellRequest)
        assert result.cmd == ["echo", "hello"]
        assert result.cwd == "/workspace"
        assert result.allow_failure is False
        assert result.debug_tag == "run_test_problem"

    def test_create_run_request_with_failure_allowed(self, factory, mock_context, mock_env_manager):
        """Test creating run request with failure allowed"""
        step = Step(type=StepType.RUN, cmd=["echo", "hello"], allow_failure=True)

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, ShellRequest)
        assert result.allow_failure is True

    def test_create_python_request(self, factory, mock_context, mock_env_manager):
        """Test creating python request"""
        step = Step(type=StepType.PYTHON, cmd=["print('hello')", "x = 1"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, PythonRequest)
        assert result.code_or_file == ["print('hello')", "x = 1"]
        assert result.cwd == "/workspace"
        assert result.debug_tag == "python_test_problem"

    def test_create_request_empty_cmd(self, factory, mock_context, mock_env_manager):
        """Test creating requests with empty command list"""
        step = Step(type=StepType.MKDIR, cmd=[])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == ""


class TestCreateRequestFunction:
    """Test create_request backward compatibility function"""

    def test_create_request_with_infrastructure_context(self):
        """Test create_request with context that has infrastructure"""
        # Mock context with infrastructure
        context = Mock()
        context.problem_name = "test_problem"
        context.infrastructure = Mock()

        # Mock environment manager
        env_manager = Mock()
        env_manager.get_workspace_root.return_value = "/workspace"
        context.infrastructure.resolve.return_value = env_manager

        step = Step(type=StepType.MKDIR, cmd=["test_dir"])

        result = create_request(step, context)

        # Should create FileRequest through factory
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.MKDIR
        assert result.path == "test_dir"

    def test_create_request_without_infrastructure_context(self):
        """Test create_request with context without infrastructure"""
        # Mock context without infrastructure attribute
        context = Mock()
        context.problem_name = "test_problem"
        del context.infrastructure  # Ensure infrastructure attribute doesn't exist

        step = Step(type=StepType.MKDIR, cmd=["test_dir"])

        result = create_request(step, context)

        # Should return None for backward compatibility
        assert result is None
