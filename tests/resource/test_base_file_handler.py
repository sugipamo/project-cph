import pytest
from src.env.resource.file.base_file_handler import BaseFileHandler
from src.context.execution_context import ExecutionContext


class MockFileHandler(BaseFileHandler):
    """Concrete implementation for testing abstract methods"""
    
    def read(self, relative_path: str):
        return f"read:{relative_path}"
    
    def write(self, relative_path: str, content: str):
        return f"write:{relative_path}:{content}"
    
    def exists(self, relative_path: str):
        return f"exists:{relative_path}"
    
    def copy(self, relative_path: str, target_path: str):
        return f"copy:{relative_path}->{target_path}"
    
    def remove(self, relative_path: str):
        return f"remove:{relative_path}"
    
    def move(self, src_path: str, dst_path: str):
        return f"move:{src_path}->{dst_path}"
    
    def copytree(self, src_path: str, dst_path: str):
        return f"copytree:{src_path}->{dst_path}"
    
    def rmtree(self, dir_path: str):
        return f"rmtree:{dir_path}"


class DummyConfig:
    pass


def test_base_file_handler_init():
    config = DummyConfig()
    handler = MockFileHandler(config)
    assert handler.config == config
    assert handler.const_handler is None


def test_base_file_handler_init_with_const_handler():
    config = DummyConfig()
    const_handler = "dummy_const_handler"
    handler = MockFileHandler(config, const_handler)
    assert handler.config == config
    assert handler.const_handler == const_handler


def test_base_file_handler_abstract_methods():
    """Test that all abstract methods are implemented and work"""
    config = DummyConfig()
    handler = MockFileHandler(config)
    
    assert handler.read("test.txt") == "read:test.txt"
    assert handler.write("test.txt", "content") == "write:test.txt:content"
    assert handler.exists("test.txt") == "exists:test.txt"
    assert handler.copy("src.txt", "dst.txt") == "copy:src.txt->dst.txt"
    assert handler.remove("test.txt") == "remove:test.txt"
    assert handler.move("src.txt", "dst.txt") == "move:src.txt->dst.txt"
    assert handler.copytree("src_dir", "dst_dir") == "copytree:src_dir->dst_dir"
    assert handler.rmtree("test_dir") == "rmtree:test_dir"


def test_base_file_handler_cannot_instantiate():
    """Test that BaseFileHandler cannot be instantiated directly"""
    config = DummyConfig()
    
    with pytest.raises(TypeError):
        BaseFileHandler(config)