import os
import pytest
from unittest.mock import MagicMock, patch
from src.environment.test_environment import TestEnvFileOpsMixin, DockerTestExecutionEnvironment

class DummyFileOperator:
    def __init__(self):
        self.called = []
        self.files = set()
    def exists(self, path):
        self.called.append(('exists', path))
        return path in self.files
    def makedirs(self, path):
        self.called.append(('makedirs', path))
        self.files.add(path)
    def copytree(self, src, dst):
        self.called.append(('copytree', src, dst))
        self.files.add(dst)
    def copy(self, src, dst):
        self.called.append(('copy', src, dst))
        self.files.add(dst)
    def rmtree(self, path):
        self.called.append(('rmtree', path))
    def resolve_path(self, path):
        class DummyDir:
            def __init__(self):
                self.name = 'dummy'
            def iterdir(self):
                return []
        return DummyDir()

class DummyUPM:
    def contest_current(self, *a):
        return 'src_dir'
    def contest_stocks(self, *a):
        return 'stocks_dir'

class DummyFileManager:
    def __init__(self):
        self.file_operator = DummyFileOperator()

class DummyHandler:
    def build(self, *args, **kwargs):
        return True, '', ''
    def run(self, *args, **kwargs):
        return True, 'out', 'err'

class DummyCtl:
    def remove_container(self, name): pass
    def start_container(self, name, image, opts): pass
    def is_container_running(self, name): return True
    def run_container(self, name, image, opts): pass
    def exec_in_container(self, name, args): return True, 'stdout', 'stderr'

class DummyPool:
    def adjust(self, req): return ['c1', 'c2']

@patch('src.environment.test_environment.UnifiedPathManager')
def test_prepare_source_code_python(mock_upm):
    mixin = TestEnvFileOpsMixin()
    mixin.upm = DummyUPM()
    mixin.file_operator = DummyFileOperator()
    result = mixin.prepare_source_code('contest', 'problem', 'python')
    assert 'python' in result

@patch('src.environment.test_environment.UnifiedPathManager')
def test_prepare_test_cases(mock_upm):
    mixin = TestEnvFileOpsMixin()
    mixin.upm = DummyUPM()
    mixin.file_operator = DummyFileOperator()
    result = mixin.prepare_test_cases('contest', 'problem')
    assert 'test' in result

def test_to_container_and_host_path():
    env = DockerTestExecutionEnvironment(DummyFileManager())
    env.unified_path_manager = MagicMock()
    env.unified_path_manager.to_container_path.return_value = '/c'
    env.unified_path_manager.to_host_path.return_value = '/h'
    assert env.to_container_path('a') == '/c'
    assert env.to_host_path('b') == '/h'

@patch('src.environment.test_environment.ContainerClient')
def test_run_test_case_success(mock_ctl):
    env = DockerTestExecutionEnvironment(DummyFileManager())
    env.handlers = {'python': DummyHandler()}
    env.ctl = DummyCtl()
    ok, out, err, n = env.run_test_case('python', 'cont', 'in', 'src', retry=2)
    assert ok
    assert out == 'out'
    assert err == 'err'
    assert n == 1 or n == 2

def test_adjust_containers_updates_info():
    env = DockerTestExecutionEnvironment(DummyFileManager())
    env.pool = DummyPool()
    env.upm = MagicMock()
    env.upm.info_json.return_value = 'info.json'
    with patch('src.info_json_manager.InfoJsonManager') as mock_info:
        mock_manager = MagicMock()
        mock_info.return_value = mock_manager
        containers = env.adjust_containers({}, 'c', 'p', 'l')
        assert containers == ['c1', 'c2']
        assert mock_manager.save.called

def test_download_testcases_raises():
    env = DockerTestExecutionEnvironment(DummyFileManager())
    env.upm = MagicMock()
    env.upm.info_json.return_value = 'info.json'
    with patch('src.info_json_manager.InfoJsonManager') as mock_info:
        mock_manager = MagicMock()
        mock_manager.get_containers.return_value = []
        mock_info.return_value = mock_manager
        with pytest.raises(RuntimeError):
            env.download_testcases('url', 'dir')

def test_submit_via_ojtools_raises():
    env = DockerTestExecutionEnvironment(DummyFileManager())
    env.upm = MagicMock()
    env.upm.info_json.return_value = 'info.json'
    with patch('src.info_json_manager.InfoJsonManager') as mock_info:
        mock_manager = MagicMock()
        mock_manager.get_containers.return_value = []
        mock_info.return_value = mock_manager
        with pytest.raises(RuntimeError):
            env.submit_via_ojtools([], [], '') 