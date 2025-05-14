"""
このファイルは言語環境拡張用の基底クラスです。
独自の言語環境やバージョンを追加したい場合は、このクラスを継承して実装してください。
例: class MyLangHandler(BaseTestHandler): ...
"""
from src.input_data_loader import InputDataLoader

# --- 言語環境の基底クラス ---
class BaseLanguageConfig:
    source_file = "main.py"
    memory_limit = None
    cpu_limit = None
    time_limit = None
    run_cmd = None

# --- テスト実行ハンドラの基底クラス ---
class BaseTestHandler():
    def __init__(self, config):
        self.__config = config
        self.__exec_client = None

class LocalTestHandler(BaseTestHandler):
    def __init__(self, config):
        super().__init__(config)

    def run(self):
        run_cmd = self.run_command(self.__config.run_cmd)
        if not run_cmd or run_cmd == ["None"]:
            return False, "", "実行ファイルが見つかりません (run_cmdがNone)"
        input_data = InputDataLoader.load(file_operator, in_file, host_in_file_path)
        run_cwd = self.run_cwd
        result = exec_client.run_and_measure(container, run_cmd, cwd=run_cwd, input=input_data, image=self.config.name)
        return TestResultParser.parse(result)
    
    def build(self):
        cmd = self.build_command(self.container_path)
        if cmd is None:
            return True, '', ''
        build_cwd = self.build_cwd
        image = self.config.name
        result = self.exec_client.run_and_measure(container, cmd, cwd=build_cwd, image=image)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

class DockerTestHandler(BaseTestHandler):
    container_workspace = "/workspace"
    dockerfile_path = None
    mounts = []