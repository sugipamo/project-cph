import os
import tempfile
import shutil
import pytest
from src.environment.execution_manager_test_environment import ExecutionManagerTestEnvironment
from unittest.mock import patch, MagicMock

class DummyManager:
    def __init__(self, returncode=0, stdout='ok', stderr='', fail_times=0):
        self.calls = []
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.fail_times = fail_times
        self.counter = 0
    def run_and_measure(self, name, cmd, **kwargs):
        self.calls.append((name, cmd, kwargs))
        if self.counter < self.fail_times:
            self.counter += 1
            class Result:
                returncode = 1
                stdout = ''
                stderr = 'fail'
            return Result()
        class Result:
            returncode = self.returncode
            stdout = self.stdout
            stderr = self.stderr
        return Result()

class DummyHandler:
    def build_command(self, source_path):
        return None, source_path
    def run_command(self, source_path, artifact_path):
        return ["echo", "dummy"]
    def run(self, manager, name, in_file, source_path):
        result = manager.run_and_measure(name, ['dummy'], input='input')
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

def test_run_test_case_success(temp_dir):
    in_path = os.path.join(temp_dir, "in.txt")
    with open(in_path, "w", encoding="utf-8") as f:
        f.write("input")
    manager = DummyManager(returncode=0, stdout='ok', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=manager, handlers={'dummy': DummyHandler()})
    ok, stdout, stderr, attempt = env.run_test_case('dummy', 'testcase1', in_path, 'src.txt', retry=2)
    assert ok
    assert stdout == 'ok'
    assert attempt == 1

def test_run_test_case_retry(temp_dir):
    in_path = os.path.join(temp_dir, "in.txt")
    with open(in_path, "w", encoding="utf-8") as f:
        f.write("input")
    manager = DummyManager(returncode=0, stdout='ok', stderr='', fail_times=1)
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=manager, handlers={'dummy': DummyHandler()})
    ok, stdout, stderr, attempt = env.run_test_case('dummy', 'testcase1', in_path, 'src.txt', retry=3)
    assert ok
    assert attempt == 2
    assert manager.counter == 1

# download_testcases: 正常系
@patch('subprocess.run')
def test_download_testcases_success(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=0, stdout='downloaded', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    with patch('os.path.exists', return_value=False), \
         patch('os.makedirs') as mock_makedirs:
        env.download_testcases('http://example.com', temp_dir)
        mock_makedirs.assert_called_once_with(temp_dir, exist_ok=True)
    mock_run.assert_called_once()

# download_testcases: 既存ディレクトリあり
@patch('subprocess.run')
def test_download_testcases_existing_dir(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=0, stdout='downloaded', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    with patch('os.path.exists', return_value=True), \
         patch('shutil.rmtree') as mock_rmtree, \
         patch('os.makedirs') as mock_makedirs:
        env.download_testcases('http://example.com', temp_dir)
        mock_rmtree.assert_called_once_with(temp_dir)
        mock_makedirs.assert_called_once_with(temp_dir, exist_ok=True)
    mock_run.assert_called_once()

# download_testcases: 異常系（oj download失敗）
@patch('subprocess.run')
def test_download_testcases_fail(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error!')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    with patch('os.path.exists', return_value=False), \
         patch('os.makedirs'):
        with pytest.raises(RuntimeError):
            env.download_testcases('http://example.com', temp_dir)
    mock_run.assert_called_once()

# submit_via_ojtools: workdirが/workspaceで始まる場合・正常系
@patch('subprocess.run')
def test_submit_via_ojtools_workspace_success(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=0, stdout='ok', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    workdir = '/workspace' + temp_dir
    ok, stdout, stderr = env.submit_via_ojtools(['submit', 'arg1'], None, workdir)
    assert ok
    assert stdout == 'ok'
    assert stderr == ''
    mock_run.assert_called_once()
    called_args = mock_run.call_args[1]['cwd']
    assert called_args.startswith('.')

# submit_via_ojtools: workdirが/workspaceで始まらない場合・正常系
@patch('subprocess.run')
def test_submit_via_ojtools_nonworkspace_success(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=0, stdout='ok', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    workdir = temp_dir
    ok, stdout, stderr = env.submit_via_ojtools(['submit', 'arg1'], None, workdir)
    assert ok
    assert stdout == 'ok'
    assert stderr == ''
    mock_run.assert_called_once()
    called_args = mock_run.call_args[1]['cwd']
    assert called_args == workdir

# submit_via_ojtools: 異常系（returncode!=0）
@patch('subprocess.run')
def test_submit_via_ojtools_fail(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=1, stdout='fail', stderr='error!')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    workdir = temp_dir
    ok, stdout, stderr = env.submit_via_ojtools(['submit', 'arg1'], None, workdir)
    assert not ok
    assert stdout == 'fail'
    assert stderr == 'error!'
    mock_run.assert_called_once()

# run_test_case: 全て失敗する場合
class AlwaysFailHandler:
    def build_command(self, source_path):
        return None, source_path
    def run_command(self, source_path, artifact_path):
        return ["false"]
    def run(self, manager, name, in_file, source_path):
        return False, '', 'fail'

def test_run_test_case_all_fail(temp_dir):
    in_path = os.path.join(temp_dir, "in.txt")
    with open(in_path, "w", encoding="utf-8") as f:
        f.write("input")
    manager = DummyManager(returncode=1, stdout='', stderr='fail')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=manager, handlers={'dummy': AlwaysFailHandler()})
    ok, stdout, stderr, attempt = env.run_test_case('dummy', 'testcase1', in_path, 'src.txt', retry=3)
    assert not ok
    assert attempt == 3
    assert stderr == 'fail'

# submit_via_ojtools: argsがNoneの場合
@patch('subprocess.run')
def test_submit_via_ojtools_args_none(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=0, stdout='ok', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    workdir = temp_dir
    ok, stdout, stderr = env.submit_via_ojtools(None, None, workdir)
    assert ok
    mock_run.assert_called_once()

# submit_via_ojtools: argsが空リストの場合
@patch('subprocess.run')
def test_submit_via_ojtools_args_empty(mock_run, temp_dir):
    mock_run.return_value = MagicMock(returncode=0, stdout='ok', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=None)
    workdir = temp_dir
    ok, stdout, stderr = env.submit_via_ojtools([], None, workdir)
    assert ok
    mock_run.assert_called_once() 