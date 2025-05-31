import pytest
from src.env_integration.controller import EnvResourceController
from src.operations.file.file_request import FileOpType, FileRequest
from src.operations.docker.docker_file_request import DockerFileRequest
from src.env_resource.file.local_file_handler import LocalFileHandler
from src.env_resource.file.docker_file_handler import DockerFileHandler
import os
import tempfile
import json
import shutil
from src.context.execution_context import ExecutionContext
from src.context.resolver.config_resolver import create_config_root_from_dict

class DummyFileHandler:
    def read(self, path):
        return f"read:{path}"
    def write(self, path, content):
        return f"write:{path}:{content}"
    def exists(self, path):
        return path == "exists.txt"
    def remove(self, path):
        return f"remove:{path}"
    def move(self, src, dst):
        return f"move:{src}->{dst}"
    def copytree(self, src, dst):
        return f"copytree:{src}->{dst}"
    def rmtree(self, path):
        return f"rmtree:{path}"
    def copy(self, src, dst):
        return f"copy:{src}->{dst}"

class DummyRunHandler:
    def create_process_options(self, cmd):
        return f"run:{cmd}"

class DummyController:
    def __init__(self, language_name=None, env_type=None, env_config=None, file_handler=None, run_handler=None, const_handler=None):
        pass

def test_dependency_injection():
    env_json = {
        "dummy": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "commands": {},
            "env_types": {"local": {}}
        }
    }
    root = create_config_root_from_dict(env_json)
    env_context = ExecutionContext(
        command_type="test",
        language="dummy",
        env_type="local",
        contest_name="abc",
        problem_name="a",
        env_json=env_json,
        resolver=root
    )
    controller = EnvResourceController(
        env_context=env_context,
        file_handler=DummyFileHandler(),
        run_handler=DummyRunHandler(),
    )
    assert controller.read_file("foo.txt") == "read:foo.txt"
    assert controller.write_file("bar.txt", "abc") == "write:bar.txt:abc"
    assert controller.file_exists("exists.txt") is True
    assert controller.file_exists("notfound.txt") is False
    assert controller.remove_file("baz.txt") == "remove:baz.txt"
    assert controller.move_file("a.txt", "b.txt") == "move:a.txt->b.txt"
    assert controller.copytree("src", "dst") == "copytree:src->dst"
    assert controller.rmtree("dir") == "rmtree:dir"
    assert controller.copy_file("a", "b") == "copy:a->b"
    assert controller.create_process_options(["ls"]) == "run:['ls']"

# local/dockerの正常系は既存のtest_env_resource_controller.pyでカバーされているため、
# ここでは依存注入・異常系を中心にテストしています。 

# Removed make_env_json function as it violates DI principles by directly accessing filesystem
