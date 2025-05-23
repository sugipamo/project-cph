import pytest
from src.env.resource.utils.const_handler import ConstHandler
from pathlib import Path
from src.context.execution_context import ExecutionContext
import hashlib
import os

def make_local_config():
    return ExecutionContext(
        command_type="test",
        language="cpp",
        env_type="local",
        contest_name="abc001",
        problem_name="a",
        env_json={
            "cpp": {
                "source_file_name": "main.cpp",
                "source_file": "main.cpp",
                "contest_env_path": "./env",
                "contest_template_path": "./template",
                "contest_temp_path": "./temp"
            }
        },
        contest_current_path="contests/abc001",
        workspace_path="/tmp/workspace"
    )

def make_docker_config():
    return ExecutionContext(
        command_type="test",
        language="python",
        env_type="docker",
        contest_name="abc002",
        problem_name="a",
        env_json={
            "python": {
                "source_file_name": "main.py",
                "source_file": "main.py",
                "contest_env_path": "./env",
                "contest_template_path": "./template",
                "contest_temp_path": "./temp"
            }
        },
        contest_current_path="contests/abc002",
        workspace_path="/tmp/workspace"
    )

def test_local_const_handler_properties():
    config = make_local_config()
    handler = ConstHandler(config)
    assert handler.workspace_path == Path("/tmp/workspace")
    assert handler.contest_current_path == Path("contests/abc001")
    assert handler.source_file_name == "main.cpp"
    assert config.env_type == "local"
    assert handler.contest_env_path == Path("env")
    assert handler.contest_template_path == Path("template")
    assert handler.contest_temp_path == Path("temp")
    assert handler.test_case_path == Path("contests/abc001/test")
    assert handler.test_case_in_path == Path("contests/abc001/test/in")
    assert handler.test_case_out_path == Path("contests/abc001/test/out")

def test_local_const_handler_parse():
    config = make_local_config()
    handler = ConstHandler(config)
    s = "{contest_current}/{source_file}/{contest_env}/{contest_template}/{contest_temp}/{test_case}/{test_case_in}/{test_case_out}"
    result = handler.parse(s)
    assert "contests/abc001" in result
    assert "main.cpp" in result
    assert "env" in result
    assert "template" in result
    assert "temp" in result
    assert "test" in result
    assert "in" in result
    assert "out" in result

def test_docker_const_handler_properties(monkeypatch):
    config = make_docker_config()
    config.dockerfile = "FROM python:3.8\nRUN echo hello"
    config.oj_dockerfile = "FROM python:3.9\nRUN echo oj"
    handler = ConstHandler(config)
    assert handler.workspace_path == Path("/tmp/workspace")
    assert handler.contest_current_path == Path("contests/abc002")
    assert handler.source_file_name == "main.py"
    assert config.env_type == "docker"
    assert handler.contest_env_path == Path("env")
    assert handler.contest_template_path == Path("template")
    assert handler.contest_temp_path == Path("temp")
    assert handler.test_case_path == Path("contests/abc002/test")
    assert handler.test_case_in_path == Path("contests/abc002/test/in")
    assert handler.test_case_out_path == Path("contests/abc002/test/out")
    expected_hash = hashlib.sha256(config.dockerfile.encode("utf-8")).hexdigest()[:12]
    assert handler.image_name == f"python_{expected_hash}"
    expected_oj_hash = hashlib.sha256(config.oj_dockerfile.encode("utf-8")).hexdigest()[:12]
    assert handler.oj_image_name == f"cph_ojtools_{expected_oj_hash}"

def test_docker_const_handler_parse(monkeypatch):
    config = make_docker_config()
    monkeypatch.setattr("src.operations.file.local_file_driver.LocalFileDriver.hash_file", lambda self, path: "dummyhash")
    handler = ConstHandler(config)
    s = "{contest_current}/{source_file}/{contest_env}/{contest_template}/{contest_temp}/{test_case}/{test_case_in}/{test_case_out}"
    result = handler.parse(s)
    assert "contests/abc002" in result
    assert "main.py" in result
    assert "env" in result
    assert "template" in result
    assert "temp" in result
    assert "test" in result
    assert "in" in result
    assert "out" in result

def test_path_resolver_contest_current_path_none():
    # contest_current_pathがNoneの場合
    config = make_local_config()
    config.contest_current_path = None
    handler = ConstHandler(config)
    with pytest.raises(ValueError) as excinfo:
        _ = handler.contest_current_path
    assert "contest_current_path" in str(excinfo.value)

def test_path_resolver_contest_env_path_none():
    # env_jsonからcontest_env_pathがNoneの場合
    config = make_local_config()
    config.env_json["cpp"]["contest_env_path"] = None
    handler = ConstHandler(config)
    # contest_envディレクトリが存在する場合はValueErrorは発生しない
    # 存在しない場合のみValueErrorを期待
    found = False
    cur = os.path.abspath(os.getcwd())
    while True:
        candidate = os.path.join(cur, "contest_env")
        if os.path.isdir(candidate):
            found = True
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    if found:
        _ = handler.contest_env_path  # エラーにならないことを確認
    else:
        with pytest.raises(ValueError) as excinfo:
            _ = handler.contest_env_path
        assert "contest_env_path" in str(excinfo.value) or "contest_env_pathが自動検出できません" in str(excinfo.value)

def test_path_resolver_contest_template_path_none():
    config = make_local_config()
    config.env_json["cpp"]["contest_template_path"] = None
    handler = ConstHandler(config)
    with pytest.raises(TypeError) as excinfo:
        _ = handler.contest_template_path
    assert "str" in str(excinfo.value)

def test_path_resolver_contest_temp_path_none():
    config = make_local_config()
    config.env_json["cpp"]["contest_temp_path"] = None
    handler = ConstHandler(config)
    with pytest.raises(TypeError) as excinfo:
        _ = handler.contest_temp_path
    assert "str" in str(excinfo.value)

def test_path_resolver_contest_env_path_key_missing():
    config = make_local_config()
    del config.env_json["cpp"]["contest_env_path"]
    handler = ConstHandler(config)
    found = False
    cur = os.path.abspath(os.getcwd())
    while True:
        candidate = os.path.join(cur, "contest_env")
        if os.path.isdir(candidate):
            found = True
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    if found:
        _ = handler.contest_env_path
    else:
        with pytest.raises(ValueError) as excinfo:
            _ = handler.contest_env_path
        assert "contest_env_path" in str(excinfo.value) or "contest_env_pathが自動検出できません" in str(excinfo.value)

def test_path_resolver_contest_template_path_key_missing():
    config = make_local_config()
    del config.env_json["cpp"]["contest_template_path"]
    handler = ConstHandler(config)
    with pytest.raises(ValueError) as excinfo:
        _ = handler.contest_template_path
    assert "contest_template_path" in str(excinfo.value)

def test_path_resolver_contest_temp_path_key_missing():
    config = make_local_config()
    del config.env_json["cpp"]["contest_temp_path"]
    handler = ConstHandler(config)
    with pytest.raises(ValueError) as excinfo:
        _ = handler.contest_temp_path
    assert "contest_temp_path" in str(excinfo.value) 