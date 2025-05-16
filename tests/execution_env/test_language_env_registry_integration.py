import sys
import os
import shutil
import pytest
from src.execution_env.execution_env_registry import list_languages, get_test_handler, EnvController

@pytest.fixture(scope="module", autouse=True)
def setup_dummy_env():
    # テスト用の contest_env/dummy/env.json を作成
    os.makedirs("contest_env/dummy", exist_ok=True)
    os.makedirs("contest_current", exist_ok=True)
    with open("contest_env/__init__.py", "w") as f:
        f.write("")
    with open("contest_env/dummy/__init__.py", "w") as f:
        f.write("")
    with open("contest_env/dummy/env.json", "w") as f:
        f.write('''{
  "LANGUAGE_ID": "9999",
  "source_file": "main.dummy",
  "handlers": {
    "local": {},
    "docker": {}
  }
}''')
    yield
    shutil.rmtree("contest_env/dummy")
    if os.path.exists("contest_env/dummy/__init__.py"):
        os.remove("contest_env/dummy/__init__.py")
    if os.path.exists("contest_env/__init__.py"):
        os.remove("contest_env/__init__.py")
    if os.path.exists("contest_current"):
        shutil.rmtree("contest_current")
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

def test_envcontroller_run_local():
    ctrl = EnvController("dummy", "local")
    result = ctrl.run(["echo", "hello"])
    assert result.stdout.strip() == "hello"

# test_envcontroller_run_dockerは削除 