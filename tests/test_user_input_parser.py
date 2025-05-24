import os
import shutil
import tempfile
import json
import pytest
from src.context.user_input_parser import parse_user_input
from src.context.execution_context import ExecutionContext
from src.env.build_operations import build_mock_operations

@pytest.fixture(scope="module")
def setup_env(tmp_path_factory):
    # contest_envディレクトリを一時ディレクトリにコピー
    tmp_dir = tmp_path_factory.mktemp("contest_env")
    shutil.copytree("contest_env/python", tmp_dir / "python")
    shutil.copytree("contest_env/rust", tmp_dir / "rust")
    return str(tmp_dir)

@pytest.mark.usefixtures("setup_env")
def test_parse_python_command(setup_env):
    args = ["python", "docker", "test", "abc300", "a"]
    operations = build_mock_operations()
    ctx = parse_user_input(args, operations)
    assert ctx.language == "python"
    assert ctx.env_type == "docker"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"
    assert ctx.env_json is not None
    assert "python" in ctx.env_json
    assert ctx.contest_current_path == "./contest_current"

@pytest.mark.usefixtures("setup_env")
def test_parse_python_alias(setup_env):
    args = ["py", "local", "t", "abc300", "a"]
    operations = build_mock_operations()
    ctx = parse_user_input(args, operations)
    assert ctx.language == "python"
    assert ctx.env_type == "local"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"

@pytest.mark.usefixtures("setup_env")
def test_parse_too_many_args(setup_env):
    args = ["python", "docker", "test", "abc300", "a", "extra"]
    operations = build_mock_operations()
    with pytest.raises(ValueError) as e:
        parse_user_input(args, operations)
    assert "引数が多すぎます" in str(e.value)

@pytest.mark.usefixtures("setup_env")
def test_parse_missing_required(setup_env):
    # 言語指定なし
    args = ["docker", "test", "abc300", "a"]
    operations = build_mock_operations()
    with pytest.raises(ValueError) as e:
        parse_user_input(args, operations)
    assert "引数が多すぎます" in str(e.value) 