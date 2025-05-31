"""
Base test class with common utilities
"""
import pytest
from src.operations.di_container import DIContainer
from src.operations.mock.mock_file_driver import MockFileDriver
from src.operations.mock.mock_shell_driver import MockShellDriver
from src.operations.mock.mock_docker_driver import MockDockerDriver


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
        di = DIContainer()
        di.register("file_driver", lambda: MockFileDriver())
        di.register("shell_driver", lambda: MockShellDriver())
        di.register("docker_driver", lambda: MockDockerDriver())
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