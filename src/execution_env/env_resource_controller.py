from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import DockerConstHandler, LocalConstHandler
from src.operations.di_container import DIContainer
from src.execution_env.run_plan_loader import load_env_json

class EnvResourceController:
    def __init__(self, language_name=None, env_type=None, env_config=None, file_handler=None, run_handler=None, const_handler=None):
        # テスト用: 依存注入があればそれを使う
        if file_handler or run_handler or const_handler:
            self.language_name = language_name
            self.env_type = env_type
            self.const_handler = const_handler
            self.run_handler = run_handler
            self.file_handler = file_handler
            self.env_config = env_config if env_config is not None else {}
            return
        self.language_name = language_name
        self.env_type = env_type
        # env_configは必ずパース済みデータとして渡す
        if env_config is None:
            raise ValueError("env_config must be provided (parsed config dict)")
        self.env_config = env_config
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

    @classmethod
    def from_plan(cls, plan):
        """
        RunPlanからEnvResourceControllerを生成するファクトリメソッド。
        env_jsonのロードやenv_configのdict生成もここでまとめる。
        """
        env_json = load_env_json(plan.language, plan.env)
        lang_conf = env_json.get(plan.language, {})
        env_types = lang_conf.get("env_types", {})
        env_type_conf = env_types.get(plan.env, {})
        env_config = dict(lang_conf)
        env_config["env_type"] = plan.env
        env_config["contest_current_path"] = lang_conf.get("contest_current_path", ".")
        env_config["source_file"] = lang_conf.get("source_file")
        env_config["contest_env_path"] = lang_conf.get("contest_env_path", "env")
        env_config["contest_template_path"] = lang_conf.get("contest_template_path", "template")
        env_config["contest_temp_path"] = lang_conf.get("contest_temp_path", "temp")
        env_config["language"] = plan.language
        env_config["env_type_conf"] = env_type_conf
        env_config["language_id"] = lang_conf.get("language_id")
        env_config["dockerfile_path"] = env_type_conf.get("dockerfile_path")
        return cls(language_name=plan.language, env_type=plan.env, env_config=env_config)

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

        print(self.const_handler.source_file_path)
        src = str(self.const_handler.source_file_path)
        # コピー先: workspace直下 or contest_temp_path等、要件に応じて変更可
        # ここでは例としてworkspace直下にコピー
        dst = str(self.const_handler.workspace / self.const_handler.source_file_path.name)
        return self.copy_file(src, dst)

    def get_build_commands(self):
        """
        env_configやconst_handlerを使ってbuild_cmdをパース・展開（parse_with_workspaceを利用）
        """
        env_type_conf = self.env_config.get("env_type_conf", {})
        build_cmds = env_type_conf.get("build_cmd", [])
        return [
            [self.const_handler.parse_with_workspace(str(x)) for x in build_cmd]
            for build_cmd in build_cmds
        ]

    def get_run_command(self):
        """
        env_configやconst_handlerを使ってrun_cmdをパース・展開（parse_with_workspaceを利用）
        """
        env_type_conf = self.env_config.get("env_type_conf", {})
        run_cmd = env_type_conf.get("run_cmd", [])
        return [self.const_handler.parse_with_workspace(str(x)) for x in run_cmd]

def get_resource_handler(language: str, env: str):
    return EnvResourceController(language, env)

