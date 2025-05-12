from src.path_manager.common_paths import HOST_PROJECT_ROOT, CONTAINER_WORKSPACE
from src.execution_env.language_env_profile import LANGUAGE_ENVS
import os

class GenericTestHandler:
    def __init__(self, language, env_type):
        self.config = LANGUAGE_ENVS[language]()

    def build_command(self, temp_source_path):
        """
        ビルドコマンドを返す（実行は外部に委譲）
        """
        if self.config.build_cmd:
            cmd = [c.format(source=str(temp_source_path)) for c in self.config.build_cmd]
            return cmd
        else:
            return None

    def get_bin_path(self, temp_source_path):
        if self.config.name == "rust":
            return os.path.join(temp_source_path, "target/release/rust")
        elif self.config.name in ("python", "pypy"):
            return temp_source_path
        elif self.config.bin_path:
            return os.path.join(temp_source_path, self.config.bin_path)
        else:
            return temp_source_path

    def run_command(self, temp_source_path):
        """
        実行コマンドを返す（実行は外部に委譲）
        """
        bin_path = self.get_bin_path(temp_source_path)
        cmd = [c.format(source=str(temp_source_path), bin_path=bin_path) for c in self.config.run_cmd]
        return cmd

# HANDLERSの生成例（local環境用）
HANDLERS = {
    "python": GenericTestHandler("python", "local"),
    "pypy": GenericTestHandler("pypy", "local"),
    "rust": GenericTestHandler("rust", "local"),
} 