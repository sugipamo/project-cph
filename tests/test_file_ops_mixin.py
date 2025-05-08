import os
import shutil
import tempfile
import pytest
from src.environment.test_environment import TestEnvFileOpsMixin

class DummyFileOperator:
    def __init__(self, base_dir):
        self.base_dir = base_dir
    def exists(self, path):
        return os.path.exists(os.path.join(self.base_dir, path))
    def makedirs(self, path):
        os.makedirs(os.path.join(self.base_dir, path), exist_ok=True)
    def copy(self, src, dst):
        shutil.copy(os.path.join(self.base_dir, src), os.path.join(self.base_dir, dst))
    def copytree(self, src, dst):
        shutil.copytree(os.path.join(self.base_dir, src), os.path.join(self.base_dir, dst), dirs_exist_ok=True)
    def rmtree(self, path):
        shutil.rmtree(os.path.join(self.base_dir, path))
    def resolve_path(self, path):
        return (os.path.join(self.base_dir, path))

class DummyEnv(TestEnvFileOpsMixin):
    def __init__(self, base_dir):
        self.file_operator = DummyFileOperator(base_dir)
        self.upm = self
    def contest_current(self, *args):
        # e.g. ('python', 'main.py') -> 'src/python/main.py'
        return os.path.join(*args)

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

def test_prepare_source_code_python(temp_dir):
    env = DummyEnv(temp_dir)
    # テスト用ファイル作成
    src_dir = os.path.join(temp_dir, 'python')
    os.makedirs(src_dir)
    with open(os.path.join(src_dir, 'main.py'), 'w') as f:
        f.write('print("hello")')
    # 実行
    dst = env.prepare_source_code('contest', 'problem', 'python')
    assert os.path.exists(os.path.join(temp_dir, dst))
    assert os.path.exists(os.path.join(temp_dir, '.temp/python/main.py'))

def test_prepare_source_code_rust(temp_dir):
    env = DummyEnv(temp_dir)
    src_dir = os.path.join(temp_dir, 'rust')
    os.makedirs(src_dir)
    with open(os.path.join(src_dir, 'main.rs'), 'w') as f:
        f.write('fn main() {}')
    # targetディレクトリも作成
    target_dir = os.path.join(src_dir, 'target')
    os.makedirs(target_dir)
    with open(os.path.join(target_dir, 'dummy'), 'w') as f:
        f.write('dummy')
    dst = env.prepare_source_code('contest', 'problem', 'rust')
    assert os.path.exists(os.path.join(temp_dir, dst))
    assert os.path.exists(os.path.join(temp_dir, '.temp/rust/main.rs'))
    assert os.path.exists(os.path.join(temp_dir, '.temp/rust/target/dummy'))

def test_prepare_test_cases(temp_dir):
    env = DummyEnv(temp_dir)
    test_dir = os.path.join(temp_dir, 'test')
    os.makedirs(test_dir)
    with open(os.path.join(test_dir, 'sample.in'), 'w') as f:
        f.write('1 2 3')
    dst = env.prepare_test_cases('contest', 'problem')
    assert os.path.exists(os.path.join(temp_dir, dst))
    assert os.path.exists(os.path.join(temp_dir, '.temp/test/sample.in')) 