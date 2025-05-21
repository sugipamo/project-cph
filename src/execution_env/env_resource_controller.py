from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import ConstHandler
from src.operations.composite_request import CompositeRequest
from src.operations.di_container import DIContainer
from src.execution_context.execution_context import ExecutionContext

class EnvResourceController:
    def __init__(self, env_context: ExecutionContext, file_handler, run_handler, const_handler):
        self.env_context = env_context
        self.language_name = env_context.language
        self.env_type = env_context.env_type
        self.const_handler = const_handler
        self.run_handler = run_handler
        self.file_handler = file_handler

    @classmethod
    def from_context(cls, env_context):
        """
        EnvContextからEnvResourceControllerを生成するファクトリメソッド。
        DIセットアップもここで行う。
        """
        container = DIContainer()
        container.register("ConstHandler", lambda: ConstHandler(env_context))
        container.register("LocalRunHandler", lambda: LocalRunHandler(env_context, container.resolve("ConstHandler")))
        container.register("DockerRunHandler", lambda: DockerRunHandler(env_context, container.resolve("ConstHandler")))
        container.register("LocalFileHandler", lambda: LocalFileHandler(env_context, container.resolve("ConstHandler")))
        container.register("DockerFileHandler", lambda: DockerFileHandler(env_context, container.resolve("ConstHandler")))
        const_handler = container.resolve("ConstHandler")
        if env_context.env_type.lower() == "docker":
            run_handler = container.resolve("DockerRunHandler")
            file_handler = container.resolve("DockerFileHandler")
        else:
            run_handler = container.resolve("LocalRunHandler")
            file_handler = container.resolve("LocalFileHandler")
        return cls(env_context, file_handler, run_handler, const_handler)

    def create_process_options(self, cmd: list):
        return self.run_handler.create_process_options(cmd)

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