"""
Base test class with common utilities
"""
import pytest

from src.infrastructure.di_container import DIContainer
from src.infrastructure.mock.mock_docker_driver import MockDockerDriver
from src.infrastructure.mock.mock_file_driver import MockFileDriver
from src.infrastructure.mock.mock_shell_driver import MockShellDriver


class BaseTest:
    """Base test class with common setup and utilities"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method called before each test method"""
        self.setup_test()

    def setup_test(self):
        """Override this method in subclasses for custom setup"""
        pass

    def create_mock_di_container(self) -> DIContainer:
        """Create a DIContainer with mock drivers"""
        from pathlib import Path
        di = DIContainer()
        # Create singleton instances to maintain state across multiple resolve() calls
        mock_file_driver = MockFileDriver(base_dir=Path.cwd())
        mock_shell_driver = MockShellDriver()
        mock_docker_driver = MockDockerDriver()

        di.register("file_driver", lambda: mock_file_driver)
        di.register("shell_driver", lambda: mock_shell_driver)
        di.register("docker_driver", lambda: mock_docker_driver)
        return di

    def create_test_context(self, **kwargs):
        """Create a test execution context"""
        default_context = {
            "command_type": "test",
            "language": "python",
            "contest_name": "test_contest",
            "problem_name": "a",
            "env_type": "local",
            "env_json": {
                "python": {
                    "workspace_path": "/tmp/test",
                    "contest_current_path": "/tmp/test/contest",
                    "commands": {
                        "test": {"steps": []}
                    },
                    "env_types": {"local": {}}
                }
            }
        }
        default_context.update(kwargs)

        from src.context.execution_context import ExecutionContext
        return ExecutionContext(**default_context)

    def assert_request_type(self, request, expected_type):
        """Assert that request is of expected type"""
        assert isinstance(request, expected_type), f"Expected {expected_type}, got {type(request)}"

    def assert_mock_operation(self, mock_driver, operation, *args):
        """Assert that mock driver recorded specific operation"""
        operations = getattr(mock_driver, 'operations', [])
        found = any(op[0] == operation and all(arg in op for arg in args) for op in operations)
        assert found, f"Operation {operation} with args {args} not found in {operations}"
