from src.operations.di_container import DIContainer
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_driver import LocalDockerDriver
from src.env_factories.unified_factory import UnifiedCommandRequestFactory
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
    # Unified factory instead of individual factories
    operations.register('UnifiedCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    # Legacy factory names for backward compatibility - all point to UnifiedFactory
    operations.register('ShellCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('DockerCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('CopyCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('OjCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('RemoveCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('BuildCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('PythonCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('MkdirCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('TouchCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('RmtreeCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('MoveCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('MoveTreeCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
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
    # Unified factory
    operations.register('UnifiedCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    # Legacy factory names for backward compatibility
    operations.register('ShellCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('DockerCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('CopyCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('OjCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('RemoveCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('BuildCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('PythonCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('MkdirCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('TouchCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('RmtreeCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('MoveCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    operations.register('MoveTreeCommandRequestFactory', lambda: UnifiedCommandRequestFactory)
    # DockerRequest, DockerOpType
    operations.register('DockerRequest', lambda: DockerRequest)
    operations.register('DockerOpType', lambda: DockerOpType)
    return operations