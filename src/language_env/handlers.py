from .profiles import get_profile

class BaseTestHandler:
    def __init__(self, language, env_type):
        self.profile = get_profile(language, env_type)
        self.config = self.profile.language_config

    def prepare_environment(self, *args, **kwargs):
        """環境ごとの前準備（必要ならオーバーライド）"""
        pass

    def build_command(self, temp_source_path):
        if self.config.build_cmd:
            return [c.format(source=str(temp_source_path)) for c in self.config.build_cmd]
        return None

    def get_bin_path(self, temp_source_path):
        return temp_source_path

    def run_command(self, temp_source_path):
        bin_path = self.get_bin_path(temp_source_path)
        return [c.format(source=str(temp_source_path), bin_path=bin_path) for c in self.config.run_cmd]

    def get_build_cwd(self, source_path):
        import os
        return os.path.dirname(source_path)

    def get_run_cwd(self, source_path):
        import os
        return os.path.dirname(source_path)

    def run(self, exec_client, container, in_file, source_path, artifact_path=None, host_in_file=None):
        """
        テストケースを実行する共通メソッド。必要に応じて各handlerでオーバーライド。
        """
        import os
        run_cmd = self.run_command(source_path)
        if not run_cmd or run_cmd == ["None"]:
            return False, "", "実行ファイルが見つかりません (run_cmdがNone)"
        # 入力データの読み込み
        if host_in_file and os.path.exists(host_in_file):
            with open(host_in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
        elif os.path.exists(in_file):
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
        else:
            input_data = ""
        run_cwd = self.get_run_cwd(source_path)
        # exec_clientはrun_and_measure互換APIを持つ想定
        result = exec_client.run_and_measure(container, run_cmd, cwd=run_cwd, input=input_data, image=self.profile.language)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

    def build(self, exec_client, container, source_path):
        """
        ビルド処理を実行する共通メソッド。必要に応じて各handlerでオーバーライド。
        """
        cmd = self.build_command(source_path)
        if cmd is None:
            return True, '', ''
        build_cwd = self.get_build_cwd(source_path)
        image = self.profile.language
        result = exec_client.run_and_measure(container, cmd, cwd=build_cwd, image=image)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

# --- Local/Container用の基底クラス ---
class LocalTestHandler(BaseTestHandler):
    pass

class ContainerTestHandler(BaseTestHandler):
    pass

# --- 言語ごとのハンドラ ---
class PythonLocalTestHandler(LocalTestHandler):
    pass

class PythonContainerTestHandler(ContainerTestHandler):
    pass

class PypyLocalTestHandler(LocalTestHandler):
    pass

class RustHandler(BaseTestHandler):
    def get_bin_path(self, temp_source_path):
        import os
        return os.path.join(temp_source_path, "target/release/rust")
    def get_build_cwd(self, source_path):
        return source_path
    def get_run_cwd(self, source_path):
        return source_path

class RustLocalTestHandler(RustHandler, LocalTestHandler):
    pass

class RustContainerTestHandler(RustHandler, ContainerTestHandler):
    pass

# --- HANDLERS ---
HANDLERS = {
    ("python", "local"): PythonLocalTestHandler("python", "local"),
    ("python", "docker"): PythonContainerTestHandler("python", "docker"),
    ("pypy", "local"): PypyLocalTestHandler("pypy", "local"),
    ("rust", "local"): RustLocalTestHandler("rust", "local"),
    ("rust", "docker"): RustContainerTestHandler("rust", "docker"),
}

def get_handler(language, env_type):
    return HANDLERS[(language, env_type)] 