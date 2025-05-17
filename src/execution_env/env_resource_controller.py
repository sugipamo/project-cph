from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import DockerConstHandler, LocalConstHandler
from src.operations.di_container import DIContainer

class EnvResourceController:
    def __init__(self, language_name=None, env_type=None, env_config=None, file_handler=None, run_handler=None, const_handler=None):
        # テスト用: 依存注入があればそれを使う
        if file_handler or run_handler or const_handler:
            self.language_name = language_name
            self.env_type = env_type
            self.const_handler = const_handler
            self.run_handler = run_handler
            self.file_handler = file_handler
            return
        self.language_name = language_name
        self.env_type = env_type
        # env_configは必ずパース済みデータとして渡す
        if env_config is None:
            raise ValueError("env_config must be provided (parsed config dict)")
        # DIコンテナのセットアップ
        container = DIContainer()
        # provider登録
        container.register("LocalConstHandler", lambda: LocalConstHandler(env_config))
        container.register("DockerConstHandler", lambda: DockerConstHandler(env_config))
        container.register("LocalRunHandler", lambda: LocalRunHandler(env_config, container.resolve("LocalConstHandler")))
        container.register("DockerRunHandler", lambda: DockerRunHandler(env_config, container.resolve("DockerConstHandler")))
        container.register("LocalFileHandler", lambda: LocalFileHandler(env_config, container.resolve("LocalConstHandler")))
        container.register("DockerFileHandler", lambda: DockerFileHandler(env_config, container.resolve("DockerConstHandler")))
        # HandlerのDI取得
        if env_config["env_type"].lower() == "docker":
            self.const_handler = container.resolve("DockerConstHandler")
            self.run_handler = container.resolve("DockerRunHandler")
            self.file_handler = container.resolve("DockerFileHandler")
        else:
            self.const_handler = container.resolve("LocalConstHandler")
            self.run_handler = container.resolve("LocalRunHandler")
            self.file_handler = container.resolve("LocalFileHandler")

    def create_process_options(self, cmd: list, driver=None):
        return self.run_handler.create_process_options(cmd, driver=driver)

    def read_file(self, relative_path: str) -> str:
        return self.file_handler.read(relative_path)

    def write_file(self, relative_path: str, content: str):
        return self.file_handler.write(relative_path, content)

    def file_exists(self, relative_path: str) -> bool:
        return self.file_handler.exists(relative_path)

    def remove_file(self, relative_path: str):
        return self.file_handler.remove(relative_path)

    def move_file(self, src_path: str, dst_path: str):
        return self.file_handler.move(src_path, dst_path)

    def copytree(self, src_path: str, dst_path: str):
        return self.file_handler.copytree(src_path, dst_path)

    def rmtree(self, dir_path: str):
        return self.file_handler.rmtree(dir_path)

    def copy_file(self, src_path: str, dst_path: str):
        return self.file_handler.copy(src_path, dst_path)

def get_resource_handler(language: str, env: str):
    return EnvResourceController(language, env)

