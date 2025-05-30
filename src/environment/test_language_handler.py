from src.path_manager.unified_path_manager import UnifiedPathManager
import os
HOST_PROJECT_ROOT = __import__('os').path.abspath('.')
CONTAINER_WORKSPACE = '/workspace'
upm = UnifiedPathManager(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE)

class TestLanguageHandler:
    def build(self, manager, name, temp_source_path):
        # Python, Pypyはビルド不要なので常に成功扱い
        return True, "", ""
    def run(self, manager, name, in_file, temp_source_path, host_in_file=None):
        raise NotImplementedError

class PythonTestHandler(TestLanguageHandler):
    def build(self, manager, name, temp_source_path):
        return True, "", ""
    def run(self, manager, name, in_file, temp_source_path, host_in_file=None):
        # managerがContainerClientならコンテナ内で実行
        if hasattr(manager, 'exec_in_container'):
            # host_in_fileから内容を読む
            if host_in_file is None:
                raise ValueError("host_in_file must be provided for container execution")
            with open(host_in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            cmd = ["python3", temp_source_path]
            result = manager.exec_in_container(name, cmd, stdin=input_data)
            ok = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            return ok, stdout, stderr
        else:
            # ローカル実行用: main.pyにinputを渡して実行
            cmd = ["python3", temp_source_path]
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            result = manager.run_and_measure(name, cmd, timeout=None, input=input_data)
            ok = result.returncode == 0
            return ok, result.stdout, result.stderr

class PypyTestHandler(TestLanguageHandler):
    def build(self, manager, name, temp_source_path):
        return True, "", ""
    def run(self, manager, name, in_file, temp_source_path, host_in_file=None):
        if hasattr(manager, 'exec_in_container'):
            if host_in_file is None:
                raise ValueError("host_in_file must be provided for container execution")
            with open(host_in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            cmd = ["pypy3", temp_source_path]
            result = manager.exec_in_container(name, cmd, stdin=input_data)
            ok = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            return ok, stdout, stderr
        else:
            cmd = ["pypy3", temp_source_path]
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            result = manager.run_and_measure(name, cmd, timeout=None, input=input_data)
            ok = result.returncode == 0
            return ok, result.stdout, result.stderr

class RustTestHandler(TestLanguageHandler):
    def build(self, manager, name, temp_source_path):
        # temp_source_pathは.temp/rustディレクトリ
        cargo_dir = os.path.abspath(temp_source_path)
        cmd = ["cargo", "build", "--release"]
        result = manager.run_and_measure(name, cmd, timeout=None, cwd=cargo_dir)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr
    def run(self, manager, name, in_file, temp_source_path, host_in_file=None):
        cargo_dir = os.path.abspath(temp_source_path)
        bin_path = os.path.join(cargo_dir, "target/release/rust")
        if hasattr(manager, 'exec_in_container'):
            if host_in_file is None:
                raise ValueError("host_in_file must be provided for container execution")
            with open(host_in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            cmd = [bin_path]
            result = manager.exec_in_container(name, cmd, stdin=input_data)
            ok = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            return ok, stdout, stderr
        else:
            cmd = [bin_path]
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            result = manager.run_and_measure(name, cmd, timeout=None, input=input_data)
            ok = result.returncode == 0
            return ok, result.stdout, result.stderr

HANDLERS = {
    "python": PythonTestHandler(),
    "pypy": PypyTestHandler(),
    "rust": RustTestHandler(),
} 