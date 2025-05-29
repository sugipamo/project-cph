import pytest
from src.env.factory.copy_command_request_factory import CopyCommandRequestFactory
from src.env.step.run_step_copy import CopyRunStep
from src.operations.file.file_request import FileRequest, FileOpType
from src.context.resolver.config_resolver import ConfigNode


class MockController:
    def __init__(self):
        self.env_context = type("EnvContext", (), {
            "contest_name": "test_contest",
            "problem_name": "a",
            "language": "python",
            "command_type": "test",
            "env_type": "local"
        })()


@pytest.fixture
def factory():
    return CopyCommandRequestFactory(MockController())


def test_create_request_success(factory):
    step = CopyRunStep(type="copy", cmd=["src.txt", "dst.txt"])
    # format_stringメソッドをモック
    factory.format_string = lambda s: f"formatted_{s}"
    
    req = factory.create_request(step)
    
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "formatted_src.txt"
    assert req.dst_path == "formatted_dst.txt"


def test_create_request_wrong_type(factory):
    class WrongStep:
        pass
    
    step = WrongStep()
    with pytest.raises(TypeError) as excinfo:
        factory.create_request(step)
    assert "CopyCommandRequestFactory expects CopyRunStep" in str(excinfo.value)


def test_create_request_insufficient_args(factory):
    step = CopyRunStep(type="copy", cmd=["only_one"])
    
    with pytest.raises(ValueError) as excinfo:
        factory.create_request(step)
    assert "cmdにはsrcとdstの2つが必要です" in str(excinfo.value)


def test_create_request_from_node_success(factory):
    # Mock node with cmd
    node = ConfigNode("test", {"type": "copy", "cmd": ["src.txt", "dst.txt"]})
    cmd_node = ConfigNode("cmd", ["src.txt", "dst.txt"])
    src_node = ConfigNode(0, "src.txt")
    dst_node = ConfigNode(1, "dst.txt")
    cmd_node.next_nodes = [src_node, dst_node]
    node.next_nodes = [cmd_node]
    
    # Mock format_value method
    factory.format_value = lambda val, node: f"formatted_{val}"
    
    req = factory.create_request_from_node(node)
    
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "formatted_src.txt"
    assert req.dst_path == "formatted_dst.txt"


def test_create_request_from_node_invalid_value(factory):
    node = ConfigNode("test", "invalid")
    
    with pytest.raises(ValueError) as excinfo:
        factory.create_request_from_node(node)
    assert "Invalid node value" in str(excinfo.value)


def test_create_request_from_node_insufficient_cmd(factory):
    node = ConfigNode("test", {"type": "copy", "cmd": ["only_one"]})
    
    with pytest.raises(ValueError) as excinfo:
        factory.create_request_from_node(node)
    assert "cmdにはsrcとdstの2つが必要です" in str(excinfo.value)


def test_create_request_from_node_without_cmd_node(factory):
    # Node without cmd child node
    node = ConfigNode("test", {"type": "copy", "cmd": ["src.txt", "dst.txt"]})
    node.next_nodes = []  # No cmd_node
    
    # Mock format_value method
    factory.format_value = lambda val, node: f"fallback_{val}"
    
    req = factory.create_request_from_node(node)
    
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "fallback_src.txt"
    assert req.dst_path == "fallback_dst.txt"