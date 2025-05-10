from src.path_manager.common_paths import HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, upm
from src.language_env.profiles import get_profile
import os

class GenericTestHandler:
    def __init__(self, language, env_type):
        self.profile = get_profile(language, env_type)
        self.config = self.profile.language_config

    def build_command(self, temp_source_path):
        """
        ビルドコマンドと成果物パスを返す（実行は外部に委譲）
        """
        artifact_path = None
        if self.config.build_cmd:
            cmd = [c.format(source=str(temp_source_path)) for c in self.config.build_cmd]
            if self.config.name == "rust":
                artifact_path = os.path.join(temp_source_path, "target/release/rust")
            elif self.config.name in ("python", "pypy"):
                artifact_path = temp_source_path
            return cmd, artifact_path
        else:
            if self.config.name in ("python", "pypy"):
                artifact_path = temp_source_path
            return None, artifact_path

    def run_command(self, temp_source_path, artifact_path):
        """
        実行コマンドを返す（実行は外部に委譲）
        """
        bin_path = str(artifact_path) if artifact_path else str(self.config.bin_path or "")
        cmd = [c.format(source=str(temp_source_path), bin_path=bin_path) for c in self.config.run_cmd]
        return cmd

# HANDLERSの生成例（local環境用）
HANDLERS = {
    "python": GenericTestHandler("python", "local"),
    "pypy": GenericTestHandler("pypy", "local"),
    "rust": GenericTestHandler("rust", "local"),
} 