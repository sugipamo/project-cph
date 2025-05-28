import os
import json
import pytest
from src.context.user_input_parser import parse_user_input
from src.env.build_operations import build_mock_operations

# テスト用env.jsonデータ
PYTHON_ENV_JSON = {
    "python": {
        "commands": {
            "test": {
                "aliases": ["t"],
                "steps": []
            }
        },
        "env_types": {
            "local": {},
            "docker": {}
        },
        "aliases": ["py"],
        "contest_current_path": "./contest_current"
    }
}
RUST_ENV_JSON = {
    "rust": {
        "commands": {
            "test": {
                "aliases": [],
                "steps": []
            }
        },
        "env_types": {
            "local": {},
            "docker": {}
        },
        "aliases": [],
        "contest_current_path": "./contest_current"
    }
}

def inject_env_json_to_operations(operations):
    """
    build_mock_operationsで生成したoperationsにenv.jsonデータを注入する共通関数。
    """
    file_driver = operations.resolve("file_driver")
    file_driver.contents[file_driver.base_dir / "contest_env/python/env.json"] = json.dumps(PYTHON_ENV_JSON)
    file_driver.contents[file_driver.base_dir / "contest_env/rust/env.json"] = json.dumps(RUST_ENV_JSON)


def test_parse_python_command():
    args = ["python", "docker", "test", "abc300", "a"]
    operations = build_mock_operations()
    inject_env_json_to_operations(operations)
    ctx = parse_user_input(args, operations)
    assert ctx.language == "python"
    assert ctx.env_type == "docker"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"
    assert ctx.env_json is not None
    assert "python" in ctx.env_json
    assert ctx.contest_current_path == "./contest_current"

def test_parse_python_alias():
    args = ["py", "local", "t", "abc300", "a"]
    operations = build_mock_operations()
    inject_env_json_to_operations(operations)
    ctx = parse_user_input(args, operations)
    assert ctx.language == "python"
    assert ctx.env_type == "local"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"

def test_parse_too_many_args():
    args = ["python", "docker", "test", "abc300", "a", "extra"]
    operations = build_mock_operations()
    inject_env_json_to_operations(operations)
    with pytest.raises(ValueError) as e:
        parse_user_input(args, operations)
    assert "引数が多すぎます" in str(e.value)

def test_parse_missing_required():
    # 言語指定なし
    args = ["docker", "test", "abc300", "a"]
    operations = build_mock_operations()
    inject_env_json_to_operations(operations)
    with pytest.raises(ValueError) as e:
        parse_user_input(args, operations)
    assert "引数が多すぎます" in str(e.value)