from src.operations.di_container import DIContainer
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_driver import LocalDockerDriver
# UnifiedCommandRequestFactory has been removed
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.local_file_driver import LocalFileDriver
from pathlib import Path

def build_operations():
    """
    operations(DIContainer)をセットアップして返す
    テストや本番で共通利用できるよう最低限の依存性のみ登録する
    """
    operations = DIContainer()
    # driver
    operations.register('shell_driver', lambda: LocalShellDriver())
    operations.register('docker_driver', lambda: LocalDockerDriver())
    operations.register('file_driver', lambda: LocalFileDriver(base_dir=Path('.')))
    # Factory classes have been removed - register None for now
    # TODO: Replace with actual factory implementations when available
    operations.register('UnifiedCommandRequestFactory', lambda: None)
    # Legacy factory names for backward compatibility
    operations.register('ShellCommandRequestFactory', lambda: None)
    operations.register('DockerCommandRequestFactory', lambda: None)
    operations.register('CopyCommandRequestFactory', lambda: None)
    operations.register('OjCommandRequestFactory', lambda: None)
    operations.register('RemoveCommandRequestFactory', lambda: None)
    operations.register('BuildCommandRequestFactory', lambda: None)
    operations.register('PythonCommandRequestFactory', lambda: None)
    operations.register('MkdirCommandRequestFactory', lambda: None)
    operations.register('TouchCommandRequestFactory', lambda: None)
    operations.register('RmtreeCommandRequestFactory', lambda: None)
    operations.register('MoveCommandRequestFactory', lambda: None)
    operations.register('MoveTreeCommandRequestFactory', lambda: None)
    # DockerRequest, DockerOpType
    operations.register('DockerRequest', lambda: DockerRequest)
    operations.register('DockerOpType', lambda: DockerOpType)
    return operations

def build_mock_operations():
    """
    モック用のoperations(DIContainer)をセットアップして返す
    """
    from src.operations.mock.mock_file_driver import MockFileDriver
    from src.operations.mock.mock_docker_driver import MockDockerDriver
    from src.operations.mock.mock_shell_driver import MockShellDriver
    from pathlib import Path

    operations = DIContainer()
    # driver
    file_driver = MockFileDriver(base_dir=Path('.'))
    operations.register('shell_driver', lambda: MockShellDriver())
    operations.register('docker_driver', lambda: MockDockerDriver())
    operations.register('file_driver', lambda: file_driver)
    # Factory classes have been removed - register None for now
    # TODO: Replace with actual factory implementations when available
    operations.register('UnifiedCommandRequestFactory', lambda: None)
    # Legacy factory names for backward compatibility
    operations.register('ShellCommandRequestFactory', lambda: None)
    operations.register('DockerCommandRequestFactory', lambda: None)
    operations.register('CopyCommandRequestFactory', lambda: None)
    operations.register('OjCommandRequestFactory', lambda: None)
    operations.register('RemoveCommandRequestFactory', lambda: None)
    operations.register('BuildCommandRequestFactory', lambda: None)
    operations.register('PythonCommandRequestFactory', lambda: None)
    operations.register('MkdirCommandRequestFactory', lambda: None)
    operations.register('TouchCommandRequestFactory', lambda: None)
    operations.register('RmtreeCommandRequestFactory', lambda: None)
    operations.register('MoveCommandRequestFactory', lambda: None)
    operations.register('MoveTreeCommandRequestFactory', lambda: None)
    # DockerRequest, DockerOpType
    operations.register('DockerRequest', lambda: DockerRequest)
    operations.register('DockerOpType', lambda: DockerOpType)
    return operations