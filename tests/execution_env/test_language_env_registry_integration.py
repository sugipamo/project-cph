import sys
import os
import shutil
import pytest
from execution_env.language_env_registry import list_languages, get_test_handler, EnvController

@pytest.fixture(scope="module", autouse=True)
def setup_dummy_env():
    # テスト用の contest_env/dummy/env.py を作成
    os.makedirs("contest_env/dummy", exist_ok=True)
    with open("contest_env/__init__.py", "w") as f:
        f.write("")
    with open("contest_env/dummy/__init__.py", "w") as f:
        f.write("")
    with open("contest_env/dummy/env.py", "w") as f:
        f.write('''\
class DummyHandler:
    language_name = "dummy"
    env_type = "local"
    def __init__(self, **kwargs):
        self.called = []
    def build(self, **kwargs):
        self.called.append("build")
        return "build-ok"
    def run(self, **kwargs):
        self.called.append("run")
        return "run-ok"
    execution_env = type("ExecEnv", (), {"execution_client_class": type("Client", (), {})})()
''')
    yield
    shutil.rmtree("contest_env/dummy")
    if os.path.exists("contest_env/dummy/__init__.py"):
        os.remove("contest_env/dummy/__init__.py")
    if os.path.exists("contest_env/__init__.py"):
        os.remove("contest_env/__init__.py")
    # pycacheも消す
    pycache = "contest_env/__pycache__"
    if os.path.exists(pycache):
        shutil.rmtree(pycache)

def test_list_languages_integration():
    langs = list_languages()
    assert "dummy" in langs

def test_get_test_handler_integration():
    handler = get_test_handler("dummy", "local")
    assert handler.language_name == "dummy"
    assert handler.env_type == "local"

def test_envcontroller_integration():
    ctrl = EnvController("dummy", "local")
    assert ctrl.build() == "build-ok"
    assert ctrl.run() == "run-ok" 