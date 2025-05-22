class EnvContextWithDI:
    """
    env_contextと、それに基づき構成されたdi_containerをラップするクラス。
    driver登録責任もここで担う。
    di_containerはテスト用に外部からも注入可能。
    """
    def __init__(self, env_context, di_container):
        self.env_context = env_context
        self.di_container = di_container

    @staticmethod
    def from_context(env_context):
        """
        本番環境用のEnvContextWithDIインスタンスを生成して返す
        """
        from src.operations.di_container import DIContainer
        from src.operations.docker.docker_request import DockerRequest, DockerOpType
        from src.env.factory.shell_command_request_factory import ShellCommandRequestFactory
        from src.env.factory.docker_command_request_factory import DockerCommandRequestFactory
        from src.env.factory.copy_command_request_factory import CopyCommandRequestFactory
        from src.env.factory.oj_command_request_factory import OjCommandRequestFactory
        from src.env.factory.remove_command_request_factory import RemoveCommandRequestFactory
        from src.env.factory.build_command_request_factory import BuildCommandRequestFactory
        di_container = DIContainer()
        env_type = getattr(env_context, 'env_type', 'local').lower()
        if env_type == 'local':
            from src.operations.shell.local_shell_driver import LocalShellDriver
            di_container.register('shell_driver', lambda: LocalShellDriver())
        elif env_type == 'docker':
            from src.operations.docker.docker_driver import LocalDockerDriver
            di_container.register('docker_driver', lambda: LocalDockerDriver())
        # --- 追加依存登録 ---
        di_container.register("DockerRequest", lambda: DockerRequest)
        di_container.register("DockerOpType", lambda: DockerOpType)
        di_container.register("ShellCommandRequestFactory", lambda: ShellCommandRequestFactory)
        di_container.register("DockerCommandRequestFactory", lambda: DockerCommandRequestFactory)
        di_container.register("CopyCommandRequestFactory", lambda: CopyCommandRequestFactory)
        di_container.register("OjCommandRequestFactory", lambda: OjCommandRequestFactory)
        di_container.register("RemoveCommandRequestFactory", lambda: RemoveCommandRequestFactory)
        di_container.register("BuildCommandRequestFactory", lambda: BuildCommandRequestFactory)
        return EnvContextWithDI(env_context, di_container) 