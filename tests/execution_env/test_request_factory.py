import pytest
from src.execution_env.request_factory import (
    ShellCommandRequestFactory, CopyCommandRequestFactory
)
from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest, FileOpType

class DummyConstHandler:
    def parse(self, s):
        # 変数展開のテスト用: {var}をVARに置換
        return s.replace("{var}", "VAR")

class DummyController:
    def __init__(self):
        self.const_handler = DummyConstHandler()

# ShellCommandRequestFactoryのテスト
def test_shell_command_request_factory():
    controller = DummyController()
    factory = ShellCommandRequestFactory(controller)
    run_config = {
        "type": "shell",
        "cmd": ["echo", "{var}"]
    }
    req = factory.create_request(run_config)
    assert isinstance(req, ShellRequest)
    assert req.cmd == ["echo", "VAR"]

# CopyCommandRequestFactoryのテスト
def test_copy_command_request_factory():
    controller = DummyController()
    factory = CopyCommandRequestFactory(controller)
    run_config = {
        "type": "copy",
        "cmd": ["src/{var}.txt", "dst/{var}.txt"]
    }
    req = factory.create_request(run_config)
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "src/VAR.txt"
    assert req.dst_path == "dst/VAR.txt" 