"""
New operations builder to replace the deprecated src/env/build_operations.py
This provides the same functionality but without the deprecated factories that return None
"""
from src.operations.di_container import DIContainer
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_driver import LocalDockerDriver
from src.operations.file.local_file_driver import LocalFileDriver
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from pathlib import Path


def build_operations():
    """
    Setup and return operations (DIContainer) with essential dependencies
    Can be used in both testing and production environments
    """
    operations = DIContainer()
    
    # Register drivers
    operations.register('shell_driver', lambda: LocalShellDriver())
    operations.register('docker_driver', lambda: LocalDockerDriver())
    operations.register('file_driver', lambda: LocalFileDriver(base_dir=Path('.')))
    
    # Register essential classes (not factories that return None)
    operations.register('DockerRequest', lambda: DockerRequest)
    operations.register('DockerOpType', lambda: DockerOpType)
    
    return operations


def build_mock_operations():
    """
    Setup and return mock operations (DIContainer) for testing
    """
    from src.operations.mock.mock_file_driver import MockFileDriver
    from src.operations.mock.mock_docker_driver import MockDockerDriver
    from src.operations.mock.mock_shell_driver import MockShellDriver
    
    operations = DIContainer()
    
    # Register mock drivers
    file_driver = MockFileDriver(base_dir=Path('.'))
    operations.register('shell_driver', lambda: MockShellDriver())
    operations.register('docker_driver', lambda: MockDockerDriver())
    operations.register('file_driver', lambda: file_driver)
    
    # Register essential classes (not factories that return None)
    operations.register('DockerRequest', lambda: DockerRequest)
    operations.register('DockerOpType', lambda: DockerOpType)
    
    return operations