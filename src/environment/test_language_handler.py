from src.path_manager.common_paths import HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, upm
from src.language_env.profiles import get_profile
import os

class GenericTestHandler:
    def __init__(self, language, env_type):
        self.profile = get_profile(language, env_type)
        self.config = self.profile.language_config

    def build(self, manager, name, temp_source_path):
        if self.config.build_cmd:
            # build_cmd内のテンプレート展開
            cmd = [c.replace("{source}", temp_source_path) for c in self.config.build_cmd]
            result = manager.run_and_measure(name, cmd, timeout=None, cwd=os.path.dirname(temp_source_path))
            ok = result.returncode == 0
            return ok, result.stdout, result.stderr
        else:
            return True, "", ""

    def run(self, manager, name, in_file, temp_source_path, host_in_file=None):
        # コマンドテンプレートを展開
        bin_path = self.config.bin_path
        cmd = [c.replace("{source}", temp_source_path).replace("{bin_path}", bin_path or "") for c in self.config.run_cmd]
        input_path = host_in_file if host_in_file is not None else in_file
        with open(input_path, "r", encoding="utf-8") as f:
            input_data = f.read()
        if hasattr(manager, 'exec_in_container'):
            result = manager.exec_in_container(name, cmd, stdin=input_data)
        else:
            result = manager.run_and_measure(name, cmd, timeout=None, input=input_data)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

# HANDLERSの生成例（local環境用）
HANDLERS = {
    "python": GenericTestHandler("python", "local"),
    "pypy": GenericTestHandler("pypy", "local"),
    "rust": GenericTestHandler("rust", "local"),
} 