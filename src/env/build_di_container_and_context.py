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

def build_di_container_and_context(env_context):
    """
    env_contextからDIContainerをセットアップし、(env_context, di_container) を返す
    テストや本番で共通利用できるよう最低限の依存性のみ登録する
    """
    di_container = DIContainer()
    # driver
    di_container.register('shell_driver', lambda: LocalShellDriver())
    di_container.register('docker_driver', lambda: LocalDockerDriver())
    # ファクトリー
    di_container.register('ShellCommandRequestFactory', lambda: ShellCommandRequestFactory)
    di_container.register('DockerCommandRequestFactory', lambda: DockerCommandRequestFactory)
    di_container.register('CopyCommandRequestFactory', lambda: CopyCommandRequestFactory)
    di_container.register('OjCommandRequestFactory', lambda: OjCommandRequestFactory)
    di_container.register('RemoveCommandRequestFactory', lambda: RemoveCommandRequestFactory)
    di_container.register('BuildCommandRequestFactory', lambda: BuildCommandRequestFactory)
    di_container.register('PythonCommandRequestFactory', lambda: PythonCommandRequestFactory)
    # DockerRequest, DockerOpType
    di_container.register('DockerRequest', lambda: DockerRequest)
    di_container.register('DockerOpType', lambda: DockerOpType)
    return env_context, di_container 