import pytest
from pathlib import Path
from src.execution_env.language_env_registry import BaseTestHandler, LocalTestHandler, DockerTestHandler

# ダミー実装
class DummyHandler(BaseTestHandler):
    def run(self, cmd):
        return "run-called: " + " ".join(cmd)

def test_base_test_handler_properties():
    handler = DummyHandler(
        source_file="main.cpp",
        time_limit=2
    )
    assert handler.contest_current_path == Path("./contest_current")
    assert handler.contest_env_path == Path("./contest_env")
    assert handler.contest_template_path == Path("./contest_template")
    assert handler.contest_temp_path == Path("./.temp")
    assert handler.source_file == "main.cpp"
    assert handler.time_limit == 2

def test_base_test_handler_run():
    handler = DummyHandler()
    assert handler.run(["echo", "hello"]) == "run-called: echo hello"

# LocalTestHandler/DockerTestHandlerは抽象のままなので、
# それらを継承してrunを実装したダミークラスでテスト
class DummyLocalHandler(LocalTestHandler):
    def run(self, cmd):
        return "local-run: " + " ".join(cmd)

class DummyDockerHandler(DockerTestHandler):
    def run(self, cmd):
        return "docker-run: " + " ".join(cmd)

def test_local_test_handler():
    handler = DummyLocalHandler()
    assert handler.run(["ls", "-l"]) == "local-run: ls -l"

def test_docker_test_handler():
    handler = DummyDockerHandler()
    assert handler.run(["ls", "/"]) == "docker-run: ls /"
    assert handler.container_workspace == "/workspace"
    assert handler.memory_limit is None 