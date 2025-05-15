import sys
import os
import shutil
import pytest
from src.execution_env.language_env_registry import list_languages, get_test_handler, EnvController

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
    assert result.strip() == "hello"

def test_envcontroller_run_docker(monkeypatch):
    # docker execのコマンドをモックしてテスト
    ctrl = EnvController("dummy", "docker", config={"container_name": "dummy_container"})
    def fake_subprocess_run(cmd, capture_output, text, **kwargs):
        class Result:
            stdout = "docker-hello\n"
        # docker exec ... echo hello
        assert cmd[:4] == ["docker", "exec", "dummy_container", "echo"]
        return Result()
    import subprocess
    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)
    result = ctrl.run(["echo", "hello"])
    assert result.strip() == "docker-hello" 