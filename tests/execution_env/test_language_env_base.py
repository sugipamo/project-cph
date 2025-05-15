import pytest
from pathlib import Path
from src.execution_env.language_env_registry import BaseTestHandler, LocalTestHandler, DockerTestHandler

# ダミー実装
class DummyHandler(BaseTestHandler):
    def run(self):
        return "run-called"
    def build(self):
        return "build-called"

def test_base_test_handler_properties():
    handler = DummyHandler(
        source_file="main.cpp",
        time_limit=2,
        run_cmd="./a.out"
    )
    assert handler.contest_current_path == Path("./contest_current")
    assert handler.contest_env_path == Path("./contest_env")
    assert handler.contest_template_path == Path("./contest_template")
    assert handler.contest_temp_path == Path("./.temp")
    assert handler.source_file == "main.cpp"
    assert handler.time_limit == 2
    assert handler.run_cmd == "./a.out"

def test_base_test_handler_run_build():
    handler = DummyHandler()
    assert handler.run() == "run-called"
    assert handler.build() == "build-called"

# LocalTestHandler/DockerTestHandlerは抽象のままなので、
# それらを継承してrun/buildを実装したダミークラスでテスト
class DummyLocalHandler(LocalTestHandler):
    def run(self):
        return "local-run"
    def build(self):
        return "local-build"

class DummyDockerHandler(DockerTestHandler):
    def run(self):
        return "docker-run"
    def build(self):
        return "docker-build"

def test_local_test_handler():
    handler = DummyLocalHandler()
    assert handler.run() == "local-run"
    assert handler.build() == "local-build"

def test_docker_test_handler():
    handler = DummyDockerHandler()
    assert handler.run() == "docker-run"
    assert handler.build() == "docker-build"
    assert handler.container_workspace == "/workspace"
    assert handler.memory_limit is None 