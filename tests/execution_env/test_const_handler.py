import pytest
from src.execution_env.resource_handler.const_handler import LocalConstHandler, DockerConstHandler, EnvType
from pathlib import Path

def make_local_config():
    return {
        "contest_current_path": "contests/abc001",
        "source_file": "main.cpp",
        "contest_env_path": "env",
        "contest_template_path": "template",
        "contest_temp_path": "temp",
    }

def make_docker_config():
    return {
        "contest_current_path": "contests/abc002",
        "source_file": "main.py",
        "contest_env_path": "env_d",
        "contest_template_path": "template_d",
        "contest_temp_path": "temp_d",
        "language": "python",
        "dockerfile_path": "Dockerfile",
    }

def test_local_const_handler_properties():
    config = make_local_config()
    handler = LocalConstHandler(config, workspace="/ws")
    assert handler.workspace == Path("/ws")
    assert handler.contest_current_path == Path("contests/abc001")
    assert handler.source_file_path == Path("contests/abc001/main.cpp")
    assert handler.env_type == EnvType.LOCAL
    assert handler.contest_env_path == Path("env")
    assert handler.contest_template_path == Path("template")
    assert handler.contest_temp_path == Path("temp")
    assert handler.test_case_path == Path("contests/abc001/test")
    assert handler.test_case_in_path == Path("contests/abc001/test/in")
    assert handler.test_case_out_path == Path("contests/abc001/test/out")

def test_local_const_handler_parse():
    config = make_local_config()
    handler = LocalConstHandler(config, workspace="/ws")
    s = "{contest_current}/{source_file}/{contest_env}/{contest_template}/{contest_temp}/{test_case}/{test_case_in}/{test_case_out}"
    result = handler.parse(s)
    assert "contests/abc001" in result
    assert "main.cpp" in result
    assert "env" in result
    assert "template" in result
    assert "temp" in result
    assert "contests/abc001/test" in result
    assert "contests/abc001/test/in" in result
    assert "contests/abc001/test/out" in result

def test_local_const_handler_parse_with_workspace():
    config = make_local_config()
    handler = LocalConstHandler(config, workspace="/ws")
    s = "{contest_current}/{source_file}/{contest_env}/{contest_template}/{contest_temp}/{test_case}/{test_case_in}/{test_case_out}"
    result = handler.parse_with_workspace(s)
    assert "/ws/contests/abc001" in result
    assert "/ws/contests/abc001/main.cpp" in result
    assert "/ws/env" in result
    assert "/ws/template" in result
    assert "/ws/temp" in result
    assert "/ws/contests/abc001/test" in result
    assert "/ws/contests/abc001/test/in" in result
    assert "/ws/contests/abc001/test/out" in result

def test_docker_const_handler_properties(monkeypatch):
    config = make_docker_config()
    # Dockerfileのハッシュを固定値にする
    monkeypatch.setattr("src.operations.file.file_driver.LocalFileDriver.hash_file", lambda self, path: "dummyhash")
    handler = DockerConstHandler(config, workspace="/ws_d")
    assert handler.workspace == Path("/ws_d")
    assert handler.contest_current_path == Path("contests/abc002")
    assert handler.source_file_path == Path("contests/abc002/main.py")
    assert handler.env_type == EnvType.DOCKER
    assert handler.contest_env_path == Path("env_d")
    assert handler.contest_template_path == Path("template_d")
    assert handler.contest_temp_path == Path("temp_d")
    assert handler.test_case_path == Path("contests/abc002/test")
    assert handler.test_case_in_path == Path("contests/abc002/test/in")
    assert handler.test_case_out_path == Path("contests/abc002/test/out")
    assert handler.image_name == "python_dummyhash"
    assert handler.container_name == "cph_python_dummyhash"
    assert handler.base_image_name == "python"

def test_docker_const_handler_parse(monkeypatch):
    config = make_docker_config()
    monkeypatch.setattr("src.operations.file.file_driver.LocalFileDriver.hash_file", lambda self, path: "dummyhash")
    handler = DockerConstHandler(config, workspace="/ws_d")
    s = "{contest_current}/{source_file}/{contest_env}/{contest_template}/{contest_temp}/{test_case}/{test_case_in}/{test_case_out}"
    result = handler.parse(s)
    assert "contests/abc002" in result
    assert "main.py" in result
    assert "env_d" in result
    assert "template_d" in result
    assert "temp_d" in result
    assert "contests/abc002/test" in result
    assert "contests/abc002/test/in" in result
    assert "contests/abc002/test/out" in result

def test_docker_const_handler_parse_with_workspace(monkeypatch):
    config = make_docker_config()
    monkeypatch.setattr("src.operations.file.file_driver.LocalFileDriver.hash_file", lambda self, path: "dummyhash")
    handler = DockerConstHandler(config, workspace="/ws_d")
    s = "{contest_current}/{source_file}/{contest_env}/{contest_template}/{contest_temp}/{test_case}/{test_case_in}/{test_case_out}"
    result = handler.parse_with_workspace(s)
    assert "/ws_d/contests/abc002" in result
    assert "/ws_d/contests/abc002/main.py" in result
    assert "/ws_d/env_d" in result
    assert "/ws_d/template_d" in result
    assert "/ws_d/temp_d" in result
    assert "/ws_d/contests/abc002/test" in result
    assert "/ws_d/contests/abc002/test/in" in result
    assert "/ws_d/contests/abc002/test/out" in result 