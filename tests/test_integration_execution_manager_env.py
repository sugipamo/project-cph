import os
import tempfile
import shutil
import pytest
from src.environment.execution_manager_test_environment import ExecutionManagerTestEnvironment
from src.execution_client.execution_manager import ExecutionManager
from src.execution_client.local import LocalAsyncClient

class PythonHandler:
    def build_command(self, source_path):
        return None, source_path
    def run_command(self, source_path, artifact_path):
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
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=manager, handlers={'python': PythonHandler()})
    ok, stdout, stderr, attempt = env.run_test_case('python', 'testcase1', str(in_path), str(src_path), retry=2)
    if not ok:
        print('STDOUT:', stdout)
        print('STDERR:', stderr)
    assert ok
    assert stdout.strip() == 'hello'
    assert attempt == 1 