"""
Mock operations for testing
"""
from .mock_file_driver import MockFileDriver
from .mock_shell_driver import MockShellDriver
from .mock_shell_request import MockShellRequest

# Dummy drivers
try:
    from .dummy_file_driver import DummyFileDriver
    from .dummy_shell_driver import DummyShellDriver
    from .dummy_docker_driver import DummyDockerDriver
    dummy_exports = ['DummyFileDriver', 'DummyShellDriver', 'DummyDockerDriver']
except ImportError:
    dummy_exports = []

__all__ = [
    'MockFileDriver',
    'MockShellDriver', 
    'MockShellRequest'
] + dummy_exports