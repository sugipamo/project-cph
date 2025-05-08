import os
import tempfile
import shutil
import pytest
from src.environment.execution_manager_test_environment import ExecutionManagerTestEnvironment

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
    manager = DummyManager(returncode=0, stdout='ok', stderr='')
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=manager, handlers={'dummy': DummyHandler()})
    ok, stdout, stderr, attempt = env.run_test_case('dummy', 'testcase1', 'in.txt', 'src.txt', retry=2)
    assert ok
    assert stdout == 'ok'
    assert attempt == 1

def test_run_test_case_retry(temp_dir):
    manager = DummyManager(returncode=0, stdout='ok', stderr='', fail_times=1)
    env = ExecutionManagerTestEnvironment(file_manager=None, manager=manager, handlers={'dummy': DummyHandler()})
    ok, stdout, stderr, attempt = env.run_test_case('dummy', 'testcase1', 'in.txt', 'src.txt', retry=3)
    assert ok
    assert attempt == 2
    assert manager.counter == 1 