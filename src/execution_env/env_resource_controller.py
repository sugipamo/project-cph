from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import DockerConstHandler, LocalConstHandler
from src.operations.di_container import DIContainer
from src.execution_env.run_plan_loader import load_env_json, EnvContext

class EnvResourceController:
    def __init__(self, env_context: EnvContext, file_handler=None, run_handler=None, const_handler=None):
        self.env_context = env_context
        self.language_name = env_context.language
        self.env_type = env_context.env
        # テスト用: 依存注入があればそれを使う
        if file_handler or run_handler or const_handler:
            self.const_handler = const_handler
            self.run_handler = run_handler
            self.file_handler = file_handler
            return
        # DIコンテナのセットアップ
        container = DIContainer()
        # provider登録
        container.register("LocalConstHandler", lambda: LocalConstHandler(env_context))
        container.register("DockerConstHandler", lambda: DockerConstHandler(env_context))
        container.register("LocalRunHandler", lambda: LocalRunHandler(env_context, container.resolve("LocalConstHandler")))
        container.register("DockerRunHandler", lambda: DockerRunHandler(env_context, container.resolve("DockerConstHandler")))
        container.register("LocalFileHandler", lambda: LocalFileHandler(env_context, container.resolve("LocalConstHandler")))
        container.register("DockerFileHandler", lambda: DockerFileHandler(env_context, container.resolve("DockerConstHandler")))
        # HandlerのDI取得
        if env_context.env.lower() == "docker":
            self.const_handler = container.resolve("DockerConstHandler")
            self.run_handler = container.resolve("DockerRunHandler")
            self.file_handler = container.resolve("DockerFileHandler")
        else:
            self.const_handler = container.resolve("LocalConstHandler")
            self.run_handler = container.resolve("LocalRunHandler")
            self.file_handler = container.resolve("LocalFileHandler")

    @classmethod
    def from_context(cls, env_context):
        """
        EnvContextからEnvResourceControllerを生成するファクトリメソッド。
        """
        return cls(env_context)

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

    def prepare_sourcecode(self):
        """
        ソースコードをworkspace内の所定の場所にコピーするリクエストを返す
        """
        src = str(self.const_handler.contest_current_path / self.const_handler.source_file_name)
        dst = str(self.const_handler.workspace_path / self.const_handler.source_file_name)
        return self.copy_file(src, dst)

    def get_build_commands(self):
        """
        env_type_confやconst_handlerを使ってbuild_cmdをパース・展開（parse_with_workspaceを利用）
        """
        env_type_conf = self.env_context.env_type_conf or {}
        build_cmds = env_type_conf.get("build_cmd", [])
        return [
            [self.const_handler.parse(str(x)) for x in build_cmd]
            for build_cmd in build_cmds
        ]

    def get_run_command(self):
        """
        env_type_confやconst_handlerを使ってrun_cmdをパース・展開（parse_with_workspaceを利用）
        """
        env_type_conf = self.env_context.env_type_conf or {}
        run_cmd = env_type_conf.get("run_cmd", [])
        return [self.const_handler.parse(str(x)) for x in run_cmd]

def get_resource_handler(language: str, env: str):
    return EnvResourceController(EnvContext(language, env))

