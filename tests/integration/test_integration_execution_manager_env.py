import os
import tempfile
import shutil
import pytest
# from src.environment.execution_manager_test_environment import ExecutionManagerTestEnvironment  # 削除
from src.execution_client.execution_manager import ExecutionManager
from src.execution_client.client.local import LocalAsyncClient

class PythonHandler:
    def build_command(self, source_path):
        return None
    def run_command(self, source_path):
        import os
        return ["python3", os.path.basename(source_path)]
    def build(self, manager, name, temp_source_path):
        return True, '', ''
    def run(self, manager, name, in_file, temp_source_path):
        cmd = ["python3", os.path.basename(temp_source_path)]
        with open(in_file, "r", encoding="utf-8") as f:
            input_data = f.read()
        cwd = os.path.dirname(temp_source_path)
        result = manager.run_and_measure(name, cmd, timeout=5, input=input_data, cwd=cwd)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

# 簡易テスト環境クラス（旧ExecutionManagerTestEnvironmentの代替）
class SimpleTestEnvironment:
    def __init__(self, file_manager, manager, handlers=None):
        self.file_manager = file_manager
        self.manager = manager
        self.handlers = handlers or {"python": PythonHandler()}
    def run_test_case(self, language_name, name, in_file, source_path, retry=3):
        handler = self.handlers[language_name]
        build_cmd = handler.build_command(source_path)
        if build_cmd:
            build_proc = os.system(' '.join(build_cmd))
            if build_proc != 0:
                return False, '', '', 1
        run_cmd = handler.run_command(source_path)
        with open(in_file, "r", encoding="utf-8") as f:
            input_data = f.read()
        for attempt in range(retry):
            result = self.manager.run_and_measure(name, run_cmd, timeout=5, input=input_data, cwd=os.path.dirname(source_path))
            ok = result.returncode == 0
            if ok:
                break
        return ok, result.stdout, result.stderr, attempt+1

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

def test_python_integration(tmp_path):
    os.chdir(tmp_path)
    # テスト用pythonファイルと入力ファイルを作成
    src_path = tmp_path / 'main.py'
    with open(src_path, 'w') as f:
        f.write('print(input())')
    in_path = tmp_path / 'input.txt'
    with open(in_path, 'w') as f:
        f.write('hello\n')
    # 実行環境構築
    client = LocalAsyncClient()
    manager = ExecutionManager(client)
    env = SimpleTestEnvironment(file_manager=None, manager=manager, handlers={'python': PythonHandler()})
    ok, stdout, stderr, attempt = env.run_test_case('python', 'testcase1', str(in_path), str(src_path), retry=2)
    if not ok:
        print('STDOUT:', stdout)
        print('STDERR:', stderr)
    assert ok
    assert stdout.strip() == 'hello'
    assert attempt == 1 