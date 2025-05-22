class EnvContextWithDI:
    """
    env_contextと、それに基づき構成されたdi_containerをラップするクラス。
    driver登録責任もここで担う。
    """
    def __init__(self, env_context):
        self.env_context = env_context
        self.di_container = self._build_di_container(env_context)

    def _build_di_container(self, env_context):
        # DIContainerのインスタンス生成
        from src.operations.di_container import DIContainer
        di_container = DIContainer()
        env_type = getattr(env_context, 'env_type', 'local').lower()
        if env_type == 'local':
            from src.operations.shell.local_shell_driver import LocalShellDriver
            di_container.register('shell_driver', lambda: LocalShellDriver())
        elif env_type == 'docker':
            from src.operations.docker.docker_driver import LocalDockerDriver
            di_container.register('docker_driver', lambda: LocalDockerDriver())
        # 他driverもここで分岐・登録可能
        return di_container 