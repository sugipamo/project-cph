"""Tests for RequestFactory"""
from unittest.mock import Mock, patch

import pytest

from src.operations.factories.request_factory import RequestFactory, create_request
from src.operations.requests.docker.docker_request import DockerRequest
from src.operations.requests.file.file_request import FileRequest
from src.operations.requests.python.python_request import PythonRequest
from src.operations.requests.shell.shell_request import ShellRequest
from src.workflow.step.step import Step, StepType


def create_step_with_validation_bypass(step_type, cmd):
    """Create a Step with validation compliance"""
    # For config fallback tests, preserve empty commands
    if cmd is None:
        cmd = []

    # Ensure commands comply with Step validation rules only when needed
    valid_cmd = cmd

    # Add minimum required arguments for validation if needed (but not for config fallback tests)
    if step_type in [StepType.COPY, StepType.MOVE] and len(valid_cmd) < 2 and len(valid_cmd) > 0:
        valid_cmd = [*valid_cmd, "dummy_target"]
    elif step_type == StepType.DOCKER_EXEC and len(valid_cmd) < 2 and len(valid_cmd) > 0:
        valid_cmd = [*valid_cmd, "dummy_cmd"]
    elif step_type == StepType.DOCKER_COMMIT and len(valid_cmd) < 2 and len(valid_cmd) > 0:
        valid_cmd = [*valid_cmd, "dummy_image"]

    return Step(type=step_type, cmd=valid_cmd)


def create_step_bypassing_validation(step_type, cmd, allow_failure=False):
    """Create a Step that bypasses validation for testing config fallbacks"""
    # This is a special version for testing that bypasses Step validation
    # We directly create the Step without going through __post_init__
    step = object.__new__(Step)
    object.__setattr__(step, 'type', step_type)
    object.__setattr__(step, 'cmd', cmd)
    object.__setattr__(step, 'allow_failure', allow_failure)
    object.__setattr__(step, 'show_output', False)
    object.__setattr__(step, 'cwd', None)
    object.__setattr__(step, 'force_env_type', None)
    object.__setattr__(step, 'format_options', None)
    object.__setattr__(step, 'output_format', None)
    object.__setattr__(step, 'format_preset', None)
    object.__setattr__(step, 'when', None)
    object.__setattr__(step, 'name', None)
    object.__setattr__(step, 'auto_generated', False)
    object.__setattr__(step, 'max_workers', 1)
    return step


class TestRequestFactory:
    """Test suite for RequestFactory"""

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager"""
        config_manager = Mock()
        config_manager.resolve_config = Mock(side_effect=self._mock_resolve_config)
        self.config_values = {}
        return config_manager

    def _mock_resolve_config(self, path, type_hint):
        """Mock resolve_config method"""
        key = '.'.join(path)
        return self.config_values.get(key, f"mock_{type_hint.__name__}")

    @pytest.fixture
    def factory(self, mock_config_manager):
        """Create RequestFactory instance"""
        return RequestFactory(mock_config_manager)

    @pytest.fixture
    def factory_no_config(self):
        """Create RequestFactory instance without config manager"""
        return RequestFactory(None)

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

    def test_init_with_config_manager(self, mock_config_manager):
        """Test factory initialization with config manager"""
        factory = RequestFactory(mock_config_manager)
        assert factory.config_manager == mock_config_manager

    def test_init_without_config_manager(self):
        """Test factory initialization without config manager"""
        factory = RequestFactory(None)
        assert factory.config_manager is None

    def test_unsupported_step_type(self, factory, mock_context, mock_env_manager):
        """Test creating request from unsupported step type"""
        # Use a mock step with None type to simulate unsupported type
        step = Mock()
        step.type = None
        result = factory.create_request_from_step(step, mock_context, mock_env_manager)
        assert result is None


class TestDockerRequestCreation:
    """Test Docker request creation methods"""

    @pytest.fixture
    def factory(self):
        """Create RequestFactory instance"""
        return RequestFactory(Mock())

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

    def test_create_docker_build_request_with_tag(self, factory, mock_context, mock_env_manager):
        """Test creating docker build request with tag"""
        step = create_step_with_validation_bypass(StepType.DOCKER_BUILD,["build", "-t", "myimage:latest", "."])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.options["tag"] == "myimage:latest"
        assert result.options["context_path"] == "/workspace"
        assert result.image == "myimage:latest"

    def test_create_docker_build_request_without_tag(self, factory, mock_context, mock_env_manager):
        """Test creating docker build request without tag"""
        step = create_step_with_validation_bypass(StepType.DOCKER_BUILD,["build", "."])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.options["tag"] is None
        assert result.options["context_path"] == "/workspace"

    def test_create_docker_run_request_with_name(self, factory, mock_context, mock_env_manager):
        """Test creating docker run request with container name"""
        step = create_step_with_validation_bypass(StepType.DOCKER_RUN,["run", "--name", "mycontainer", "myimage"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container == "mycontainer"
        assert result.image == "myimage"
        assert result.options["workspace_mount"] == "/workspace"
        # assert result.debug_tag == "docker_run_test_problem"

    def test_create_docker_run_request_without_name(self, factory, mock_context, mock_env_manager):
        """Test creating docker run request without container name"""
        step = create_step_with_validation_bypass(StepType.DOCKER_RUN,["run", "myimage"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container is None
        assert result.image == "myimage"

    def test_create_docker_exec_request_with_cmd(self, factory, mock_context, mock_env_manager):
        """Test creating docker exec request with command"""
        step = create_step_with_validation_bypass(StepType.DOCKER_EXEC,["mycontainer", "ls", "-la"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container == "mycontainer"
        assert result.command == ["ls", "-la"]
        # assert result.debug_tag == "docker_exec_test_problem"

    def test_create_docker_exec_request_empty_cmd_with_config(self, mock_context, mock_env_manager):
        """Test creating docker exec request with empty command using config fallback"""
        mock_config = Mock()
        mock_config.resolve_config.side_effect = lambda path, type_hint: {
            ('request_factory_defaults', 'docker', 'container_name_fallback'): "default_container",
            ('request_factory_defaults', 'docker', 'exec_cmd_fallback'): ["bash"]
        }.get(tuple(path), None)

        factory = RequestFactory(mock_config)
        step = create_step_bypassing_validation(StepType.DOCKER_EXEC, [])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container == "default_container"
        assert result.command == ["bash"]

    def test_create_docker_exec_request_empty_cmd_no_config(self, mock_context, mock_env_manager):
        """Test creating docker exec request with empty command without config manager"""
        factory = RequestFactory(None)
        step = create_step_bypassing_validation(StepType.DOCKER_EXEC, [])

        with pytest.raises(ValueError, match="No command provided for docker exec"):
            factory.create_request_from_step(step, mock_context, mock_env_manager)

    def test_create_docker_exec_request_only_container(self, mock_context, mock_env_manager):
        """Test creating docker exec request with only container name"""
        mock_config = Mock()
        mock_config.resolve_config.return_value = ["bash"]

        factory = RequestFactory(mock_config)
        step = create_step_bypassing_validation(StepType.DOCKER_EXEC, ["mycontainer"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container == "mycontainer"
        assert result.command == ["bash"]

    def test_create_docker_commit_request(self, factory, mock_context, mock_env_manager):
        """Test creating docker commit request"""
        step = create_step_with_validation_bypass(StepType.DOCKER_COMMIT,["mycontainer", "myimage:v1"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container == "mycontainer"
        assert result.image == "myimage:v1"
        # assert result.debug_tag == "docker_commit_test_problem"

    def test_create_docker_rm_request(self, factory, mock_context, mock_env_manager):
        """Test creating docker rm request"""
        step = create_step_with_validation_bypass(StepType.DOCKER_RM,["mycontainer"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.container == "mycontainer"
        # assert result.debug_tag == "docker_rm_test_problem"

    def test_create_docker_rmi_request(self, factory, mock_context, mock_env_manager):
        """Test creating docker rmi request"""
        step = create_step_with_validation_bypass(StepType.DOCKER_RMI,["myimage:latest"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, DockerRequest)
        assert result.image == "myimage:latest"
        # assert result.debug_tag == "docker_rmi_test_problem"


class TestFileRequestCreation:
    """Test file request creation methods"""

    @pytest.fixture
    def factory(self):
        """Create RequestFactory instance"""
        return RequestFactory(Mock())

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

    def test_create_mkdir_request(self, factory, mock_context, mock_env_manager):
        """Test creating mkdir request"""
        step = create_step_with_validation_bypass(StepType.MKDIR,["/path/to/dir"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/path/to/dir"
        # assert result.debug_tag == "mkdir_test_problem"

    def test_create_touch_request(self, factory, mock_context, mock_env_manager):
        """Test creating touch request"""
        step = create_step_with_validation_bypass(StepType.TOUCH,["/path/to/file.txt"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/path/to/file.txt"
        # assert result.debug_tag == "touch_test_problem"

    def test_create_copy_request(self, factory, mock_context, mock_env_manager):
        """Test creating copy request"""
        step = create_step_with_validation_bypass(StepType.COPY,["/source/file", "/dest/file"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/source/file"
        assert result.dst_path == "/dest/file"
        # assert result.debug_tag == "copy_test_problem"

    def test_create_move_request(self, factory, mock_context, mock_env_manager):
        """Test creating move request"""
        step = create_step_with_validation_bypass(StepType.MOVE,["/source/file", "/dest/file"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/source/file"
        assert result.dst_path == "/dest/file"
        # assert result.debug_tag == "move_test_problem"

    def test_create_move_request_missing_target(self, factory, mock_context, mock_env_manager):
        """Test creating move request with missing target"""
        step = create_step_bypassing_validation(StepType.MOVE, ["/source/file"])

        with pytest.raises(ValueError, match="Copy command requires both source and target paths"):
            factory.create_request_from_step(step, mock_context, mock_env_manager)

    def test_create_move_request_empty_cmd(self, factory, mock_context, mock_env_manager):
        """Test creating move request with empty command"""
        step = create_step_bypassing_validation(StepType.MOVE, [])

        with pytest.raises(ValueError, match="Copy command requires source path"):
            factory.create_request_from_step(step, mock_context, mock_env_manager)

    def test_create_remove_request(self, factory, mock_context, mock_env_manager):
        """Test creating remove request"""
        step = create_step_with_validation_bypass(StepType.REMOVE,["/path/to/file"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/path/to/file"
        # assert result.debug_tag == "remove_test_problem"

    def test_create_remove_request_empty_cmd(self, factory, mock_context, mock_env_manager):
        """Test creating remove request with empty command"""
        step = create_step_bypassing_validation(StepType.REMOVE, [])

        with pytest.raises(ValueError, match="Remove command requires path"):
            factory.create_request_from_step(step, mock_context, mock_env_manager)

    def test_create_rmtree_request(self, factory, mock_context, mock_env_manager):
        """Test creating rmtree request"""
        step = create_step_with_validation_bypass(StepType.RMTREE,["/path/to/dir"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/path/to/dir"
        # assert result.debug_tag == "rmtree_test_problem"

    def test_create_rmtree_request_empty_cmd(self, factory, mock_context, mock_env_manager):
        """Test creating rmtree request with empty command"""
        step = create_step_bypassing_validation(StepType.RMTREE, [])

        with pytest.raises(ValueError, match="rmtree command requires path"):
            factory.create_request_from_step(step, mock_context, mock_env_manager)


class TestShellRequestCreation:
    """Test shell request creation methods"""

    @pytest.fixture
    def factory(self):
        """Create RequestFactory instance"""
        return RequestFactory(Mock())

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

    def test_create_chmod_request(self, factory, mock_context, mock_env_manager):
        """Test creating chmod request"""
        step = create_step_with_validation_bypass(StepType.CHMOD,["755", "/path/to/file"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, ShellRequest)
        assert result.cmd == ["755", "/path/to/file"]
        assert result.cwd == "/workspace"
        # assert result.debug_tag == "chmod_test_problem"

    def test_create_run_request(self, factory, mock_context, mock_env_manager):
        """Test creating run request"""
        step = create_step_with_validation_bypass(StepType.RUN,["echo", "hello"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, ShellRequest)
        assert result.cmd == ["echo", "hello"]
        assert result.cwd == "/workspace"
        # assert result.debug_tag == "run_test_problem"

    def test_create_run_request_with_allow_failure(self, factory, mock_context, mock_env_manager):
        """Test creating run request with allow_failure flag"""
        step = create_step_bypassing_validation(StepType.RUN, ["echo", "hello"], allow_failure=True)

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, ShellRequest)
        assert result.allow_failure is True


class TestPythonRequestCreation:
    """Test Python request creation methods"""

    @pytest.fixture
    def factory(self):
        """Create RequestFactory instance"""
        return RequestFactory(Mock())

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

    def test_create_python_request(self, factory, mock_context, mock_env_manager):
        """Test creating python request"""
        step = create_step_with_validation_bypass(StepType.PYTHON,["print('hello')", "x = 1"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, PythonRequest)
        assert result.code_or_file == ["print('hello')", "x = 1"]
        assert result.cwd == "/workspace"
        # assert result.debug_tag == "python_test_problem"


class TestConfigFallbacks:
    """Test configuration fallback scenarios"""

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

    def test_mkdir_with_config_fallback(self, mock_context, mock_env_manager):
        """Test mkdir with config fallback"""
        mock_config = Mock()
        mock_config.resolve_config.return_value = "/default/path"

        factory = RequestFactory(mock_config)
        step = create_step_bypassing_validation(StepType.MKDIR, [])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/default/path"
        mock_config.resolve_config.assert_called_with(
            ['request_factory_defaults', 'file', 'path_fallback'], str
        )

    def test_mkdir_without_config_no_cmd(self, mock_context, mock_env_manager):
        """Test mkdir without config manager and no command"""
        factory = RequestFactory(None)
        step = create_step_bypassing_validation(StepType.MKDIR, [])

        with pytest.raises(ValueError, match="No command provided for mkdir"):
            factory.create_request_from_step(step, mock_context, mock_env_manager)

    def test_copy_with_config_fallback(self, mock_context, mock_env_manager):
        """Test copy with config fallback for target"""
        mock_config = Mock()
        mock_config.resolve_config.return_value = "/default/target"

        factory = RequestFactory(mock_config)
        step = create_step_bypassing_validation(StepType.COPY, ["/source"])

        result = factory.create_request_from_step(step, mock_context, mock_env_manager)

        assert isinstance(result, FileRequest)
        assert result.path == "/source"
        assert result.dst_path == "/default/target"


class TestBackwardCompatibilityFunction:
    """Test backward compatibility create_request function"""

    def test_create_request_with_infrastructure(self):
        """Test create_request function with infrastructure context"""
        # Mock context with infrastructure attribute
        mock_context = Mock()
        mock_context.infrastructure.resolve.return_value = Mock()
        mock_context.infrastructure.resolve.return_value.get_workspace_root.return_value = "/workspace"

        step = create_step_with_validation_bypass(StepType.RUN,["echo", "test"])

        with patch('src.operations.factories.request_factory._factory_instance') as mock_factory:
            mock_factory.create_request_from_step.return_value = Mock()

            create_request(step, mock_context)

            mock_factory.create_request_from_step.assert_called_once()

    def test_create_request_without_infrastructure(self):
        """Test create_request function without infrastructure context"""
        mock_context = Mock()
        del mock_context.infrastructure  # Remove infrastructure attribute

        step = create_step_with_validation_bypass(StepType.RUN,["echo", "test"])

        result = create_request(step, mock_context)

        assert result is None
