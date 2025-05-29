from src.operations.di_container import DIContainer
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_driver import LocalDockerDriver
from src.env.factory.shell_command_request_factory import ShellCommandRequestFactory
from src.env.factory.docker_command_request_factory import DockerCommandRequestFactory
from src.env.factory.copy_command_request_factory import CopyCommandRequestFactory
from src.env.factory.oj_command_request_factory import OjCommandRequestFactory
from src.env.factory.remove_command_request_factory import RemoveCommandRequestFactory
from src.env.factory.build_command_request_factory import BuildCommandRequestFactory
from src.env.factory.python_command_request_factory import PythonCommandRequestFactory
from src.env.factory.mkdir_command_request_factory import MkdirCommandRequestFactory
from src.env.factory.touch_command_request_factory import TouchCommandRequestFactory
from src.env.factory.movetree_command_request_factory import MoveTreeCommandRequestFactory
from src.env.factory.rmtree_command_request_factory import RmtreeCommandRequestFactory
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
    # ファクトリー
    operations.register('ShellCommandRequestFactory', lambda: ShellCommandRequestFactory)
    operations.register('DockerCommandRequestFactory', lambda: DockerCommandRequestFactory)
    operations.register('CopyCommandRequestFactory', lambda: CopyCommandRequestFactory)
    operations.register('OjCommandRequestFactory', lambda: OjCommandRequestFactory)
    operations.register('RemoveCommandRequestFactory', lambda: RemoveCommandRequestFactory)
    operations.register('BuildCommandRequestFactory', lambda: BuildCommandRequestFactory)
    operations.register('PythonCommandRequestFactory', lambda: PythonCommandRequestFactory)
    operations.register('MkdirCommandRequestFactory', lambda: MkdirCommandRequestFactory)
    operations.register('TouchCommandRequestFactory', lambda: TouchCommandRequestFactory)
    operations.register('RmtreeCommandRequestFactory', lambda: RmtreeCommandRequestFactory)
    operations.register('MoveCommandRequestFactory', lambda: MoveCommandRequestFactory)
    operations.register('MoveTreeCommandRequestFactory', lambda: MoveTreeCommandRequestFactory)
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
    # ファクトリー（本物をそのまま登録）
    operations.register('ShellCommandRequestFactory', lambda: ShellCommandRequestFactory)
    operations.register('DockerCommandRequestFactory', lambda: DockerCommandRequestFactory)
    operations.register('CopyCommandRequestFactory', lambda: CopyCommandRequestFactory)
    operations.register('OjCommandRequestFactory', lambda: OjCommandRequestFactory)
    operations.register('RemoveCommandRequestFactory', lambda: RemoveCommandRequestFactory)
    operations.register('BuildCommandRequestFactory', lambda: BuildCommandRequestFactory)
    operations.register('PythonCommandRequestFactory', lambda: PythonCommandRequestFactory)
    operations.register('MkdirCommandRequestFactory', lambda: MkdirCommandRequestFactory)
    operations.register('TouchCommandRequestFactory', lambda: TouchCommandRequestFactory)
    operations.register('RmtreeCommandRequestFactory', lambda: RmtreeCommandRequestFactory)
    operations.register('MoveCommandRequestFactory', lambda: MoveCommandRequestFactory)
    operations.register('MoveTreeCommandRequestFactory', lambda: MoveTreeCommandRequestFactory)
    # DockerRequest, DockerOpType
    operations.register('DockerRequest', lambda: DockerRequest)
    operations.register('DockerOpType', lambda: DockerOpType)
    return operations 