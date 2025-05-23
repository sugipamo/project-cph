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
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.file.local_file_driver import LocalFileDriver
from pathlib import Path

def build_operations_and_context(env_context):
    """
    env_contextからoperations(DIContainer)をセットアップし、(env_context, operations) を返す
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
    # DockerRequest, DockerOpType
    operations.register('DockerRequest', lambda: DockerRequest)
    operations.register('DockerOpType', lambda: DockerOpType)
    return env_context, operations 