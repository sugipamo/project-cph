"""
Test unified request factory implementation
"""
import pytest

from src.application.factories.unified_request_factory import (
    FilePreparationRequestStrategy,
    FileRequestStrategy,
    PythonRequestStrategy,
    RequestCreationStrategy,
    ShellRequestStrategy,
    UnifiedRequestFactory,
    create_composite_request,
    create_request,
)
from src.domain.requests.docker.docker_request import DockerRequest
from src.domain.requests.file.file_request import FileRequest
from src.domain.requests.python.python_request import PythonRequest
from src.domain.requests.shell.shell_request import ShellRequest
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.workflow.step.step import Step, StepType


class MockContext:
    """Mock context for testing"""

    def __init__(self):
        self.env_type = "local"
        self.language = "python"
        self.contest_name = "abc300"
        self.problem_name = "a"

    def format_string(self, template: str) -> str:
        """Simple formatting for testing"""
        return template.replace("{contest_name}", self.contest_name).replace("{problem_name}", self.problem_name)

    def to_dict(self):
        """Convert context to dictionary for formatting"""
        return {
            "env_type": self.env_type,
            "language_name": self.language,
            "contest_name": self.contest_name,
            "problem_name": self.problem_name
        }


class TestRequestCreationStrategies:

    def test_file_request_strategy(self):
        """Test FileRequestStrategy"""
        strategy = FileRequestStrategy()

        # Test can_handle
        assert strategy.can_handle(StepType.MKDIR)
        assert strategy.can_handle(StepType.COPY)
        assert not strategy.can_handle(StepType.SHELL)

        # Test create_request for mkdir
        step = Step(type=StepType.MKDIR, cmd=["/tmp/test"])
        context = MockContext()
        env_manager = EnvironmentManager("local")

        request = strategy.create_request(step, context, env_manager)
        assert isinstance(request, FileRequest)
        assert request.path == "/tmp/test"
        assert request.op.name == "MKDIR"

        # Test create_request for copy
        step = Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        request = strategy.create_request(step, context, env_manager)
        assert isinstance(request, FileRequest)
        assert request.path == "src.txt"
        assert request.dst_path == "dst.txt"

    def test_shell_request_strategy(self):
        """Test ShellRequestStrategy"""
        strategy = ShellRequestStrategy()

        # Test can_handle
        assert strategy.can_handle(StepType.SHELL)
        assert not strategy.can_handle(StepType.MKDIR)

        # Test create_request
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"], cwd="/tmp")
        context = MockContext()
        env_manager = EnvironmentManager("local")

        request = strategy.create_request(step, context, env_manager)
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["echo", "hello"]
        assert request.cwd == "/tmp"
        assert request.env is None

    def test_python_request_strategy(self):
        """Test PythonRequestStrategy"""
        strategy = PythonRequestStrategy()

        # Test can_handle
        assert strategy.can_handle(StepType.PYTHON)
        assert not strategy.can_handle(StepType.SHELL)

        # Test create_request
        step = Step(type=StepType.PYTHON, cmd=["print('hello')", "print('world')"])
        context = MockContext()
        env_manager = EnvironmentManager("local")

        request = strategy.create_request(step, context, env_manager)
        assert isinstance(request, PythonRequest)
        assert "print('hello')" in request.code_or_file
        assert "print('world')" in request.code_or_file

    def test_file_preparation_request_strategy(self):
        """Test FilePreparationRequestStrategy"""
        strategy = FilePreparationRequestStrategy()

        # Test can_handle
        assert strategy.can_handle(StepType.FILE_PREPARATION)
        assert not strategy.can_handle(StepType.SHELL)

        # Test create_request with attribute-based format (new format)
        step = Step(
            type=StepType.FILE_PREPARATION,
            cmd=[],  # Empty cmd for state transition
            target_state="working",
            context={
                "contest_name": "{contest_name}",
                "problem_name": "{problem_name}",
                "language": "{language_name}"
            }
        )
        context = MockContext()
        env_manager = EnvironmentManager("local")

        request = strategy.create_request(step, context, env_manager)
        assert request is not None
        assert request.target_state == "working"
        assert request.context_params["contest_name"] == "abc300"
        assert request.context_params["problem_name"] == "a"
        assert request.context_params["language"] == "python"

        # Test create_request with cmd-based format (legacy format)
        step = Step(type=StepType.FILE_PREPARATION, cmd=["working", "contest_name=abc123", "problem_name=b"])
        request = strategy.create_request(step, context, env_manager)
        assert request is not None
        assert request.target_state == "working"
        assert request.context_params["contest_name"] == "abc123"
        assert request.context_params["problem_name"] == "b"

        # Test with empty cmd
        step = Step(type=StepType.FILE_PREPARATION, cmd=[])
        request = strategy.create_request(step, context, env_manager)
        assert request is None


class TestUnifiedRequestFactory:

    def test_factory_initialization(self):
        """Test factory initialization"""
        factory = UnifiedRequestFactory()
        assert len(factory._strategies) > 0

        # Check that all expected strategies are registered
        strategy_types = [type(s).__name__ for s in factory._strategies]
        assert "FileRequestStrategy" in strategy_types
        assert "ShellRequestStrategy" in strategy_types
        assert "PythonRequestStrategy" in strategy_types
        assert "FilePreparationRequestStrategy" in strategy_types

    def test_create_file_request(self):
        """Test creating file requests"""
        factory = UnifiedRequestFactory()
        context = MockContext()

        # Test mkdir
        step = Step(type=StepType.MKDIR, cmd=["/tmp/test"])
        request = factory.create_request_from_step(step, context, EnvironmentManager("local"))
        assert isinstance(request, FileRequest)

        # Test copy
        step = Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        request = factory.create_request_from_step(step, context, EnvironmentManager("local"))
        assert isinstance(request, FileRequest)

    def test_create_shell_request(self):
        """Test creating shell requests"""
        factory = UnifiedRequestFactory()
        context = MockContext()

        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        request = factory.create_request_from_step(step, context, EnvironmentManager("local"))
        assert isinstance(request, ShellRequest)

    def test_create_python_request(self):
        """Test creating python requests"""
        factory = UnifiedRequestFactory()
        context = MockContext()

        step = Step(type=StepType.PYTHON, cmd=["print('test')"])
        request = factory.create_request_from_step(step, context, EnvironmentManager("local"))
        assert isinstance(request, PythonRequest)

    def test_create_file_preparation_request(self):
        """Test creating state transition requests"""
        factory = UnifiedRequestFactory()
        context = MockContext()

        # Test with attribute-based format
        step = Step(
            type=StepType.FILE_PREPARATION,
            cmd=[],
            target_state="working",
            context={"contest_name": "{contest_name}"}
        )

        request = factory.create_request_from_step(step, context, EnvironmentManager("local"))
        assert request is not None
        assert request.target_state == "working"

    def test_force_local_execution(self):
        """Test force local execution"""
        factory = UnifiedRequestFactory()
        context = MockContext()

        # Create step with force_env_type
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"], force_env_type="local")

        # Use docker environment manager
        env_manager = EnvironmentManager("docker")

        request = factory.create_request_from_step(step, context, env_manager)
        assert isinstance(request, ShellRequest)
        # Should succeed even though we forced local

    def test_create_multiple_requests(self):
        """Test creating multiple requests from steps"""
        UnifiedRequestFactory()
        MockContext()

        [
            Step(type=StepType.MKDIR, cmd=["/tmp/test"]),
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.PYTHON, cmd=["print('test')"]),
        ]

        # TODO: create_requests_from_steps method needs to be implemented
        # requests = factory.create_requests_from_steps(steps, context)
        # assert len(requests) == 3
        # assert isinstance(requests[0], FileRequest)
        # assert isinstance(requests[1], ShellRequest)
        # assert isinstance(requests[2], PythonRequest)

    def test_create_composite_request(self):
        """Test creating composite request"""
        UnifiedRequestFactory()
        context = MockContext()

        steps = [
            Step(type=StepType.MKDIR, cmd=["/tmp/test"]),
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
        ]

        composite = create_composite_request(steps, context)
        assert composite is not None
        # CompositeRequest details depend on implementation

    def test_register_custom_strategy(self):
        """Test registering custom strategy"""
        factory = UnifiedRequestFactory()

        class CustomStrategy(RequestCreationStrategy):
            def can_handle(self, step_type: StepType) -> bool:
                return step_type == StepType.RESULT

            def create_request(self, step, context, env_manager):
                return None  # Custom implementation

        custom_strategy = CustomStrategy()
        factory.register_strategy(custom_strategy)

        # Verify strategy was added
        assert custom_strategy in factory._strategies


class TestGlobalFactoryFunctions:

    def test_global_create_request(self):
        """Test global create_request function"""
        context = MockContext()
        step = Step(type=StepType.MKDIR, cmd=["/tmp/test"])

        request = create_request(step, context)
        assert isinstance(request, FileRequest)


    def test_global_create_composite_request(self):
        """Test global create_composite_request function"""
        context = MockContext()
        steps = [Step(type=StepType.MKDIR, cmd=["/tmp/test"])]

        composite = create_composite_request(steps, context)
        assert composite is not None
