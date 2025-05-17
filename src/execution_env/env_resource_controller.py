from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import DockerConstHandler, LocalConstHandler
from src.operations.composite_request import CompositeRequest
from src.operations.di_container import DIContainer
from src.execution_env.run_plan_loader import EnvContext

class EnvResourceController:
    def __init__(self, env_context: EnvContext, file_handler, run_handler, const_handler):
        self.env_context = env_context
        self.language_name = env_context.language
        self.env_type = env_context.env
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
        container.register("LocalConstHandler", lambda: LocalConstHandler(env_context))
        container.register("DockerConstHandler", lambda: DockerConstHandler(env_context))
        container.register("LocalRunHandler", lambda: LocalRunHandler(env_context, container.resolve("LocalConstHandler")))
        container.register("DockerRunHandler", lambda: DockerRunHandler(env_context, container.resolve("DockerConstHandler")))
        container.register("LocalFileHandler", lambda: LocalFileHandler(env_context, container.resolve("LocalConstHandler")))
        container.register("DockerFileHandler", lambda: DockerFileHandler(env_context, container.resolve("DockerConstHandler")))
        if env_context.env.lower() == "docker":
            const_handler = container.resolve("DockerConstHandler")
            run_handler = container.resolve("DockerRunHandler")
            file_handler = container.resolve("DockerFileHandler")
        else:
            const_handler = container.resolve("LocalConstHandler")
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

    def get_build_commands(self):
        """
        build_cmdをenv_contextから直接取得し、const_handlerでパースして返す
        """

        requests = []
        for src, dst in self.env_context.build_prepare_file_moves:
            copy_req = self.copy_file(self.const_handler.parse(src), self.const_handler.parse(dst))
            requests.append(copy_req)

        for build_cmd in self.env_context.build_cmds:
            parsed_cmd = [self.const_handler.parse(str(x)) for x in build_cmd]
            requests.append(self.create_process_options(parsed_cmd))
            
        return CompositeRequest.make_composite_request(requests)

    def get_run_command(self):
        """
        run_cmdをenv_contextから直接取得し、const_handlerでパースして返す
        """
        run_cmd = self.env_context.run_cmd or []
        requests = []
        for run_prepare_file_move in self.env_context.run_prepare_file_moves:
            src = run_prepare_file_move["src"]
            dst = run_prepare_file_move["dst"]
            copy_req = self.copy_file(self.const_handler.parse(src), self.const_handler.parse(dst))
            requests.append(copy_req)

        parsed_cmd = self.create_process_options([self.const_handler.parse(str(x)) for x in run_cmd])
        return CompositeRequest.make_composite_request(requests)

def get_resource_handler(language: str, env: str):
    return EnvResourceController(EnvContext(language, env))

