import os
import json
import pytest
from src.context.user_input_parser import parse_user_input
from src.env.build_operations import build_mock_operations
from pathlib import Path

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
    py_path = Path('contest_env/python/env.json')
    rs_path = Path('contest_env/rust/env.json')
    file_driver.add(py_path, json.dumps(PYTHON_ENV_JSON))
    file_driver.add(rs_path, json.dumps(RUST_ENV_JSON))
    print(f"[DEBUG] file_driver.files after add: {file_driver.files}")
    print(f"[DEBUG] inject_env_json_to_operations: id(file_driver)={id(file_driver)}")
    return file_driver


def test_parse_python_command():
    args = ["python", "docker", "test", "abc300", "a"]
    operations = build_mock_operations()
    file_driver = inject_env_json_to_operations(operations)
    print(f"[DEBUG] test_parse_python_command: id(file_driver)={id(file_driver)}")
    print(f"[DEBUG] test_parse_python_command: id(operations.resolve('file_driver'))={id(operations.resolve('file_driver'))}")
    print(f"[DEBUG] test_parse_python_command: args={args}")
    print(f"[DEBUG] test_parse_python_command: file_driver.files={file_driver.files}")
    print(f"[DEBUG] test_parse_python_command: env_json={file_driver.contents}")
    from src.context.user_input_parser import _load_all_env_jsons, CONTEST_ENV_DIR
    env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR, operations)
    merged_env_json = {}
    for env_json in env_jsons:
        merged_env_json.update(env_json)
    print(f"[DEBUG] test_parse_python_command: merged_env_json={merged_env_json}")
    ctx = parse_user_input(args, operations)
    assert ctx.language == "python"
    assert ctx.env_type == "docker"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"
    assert ctx.env_json is not None
    assert "python" in ctx.env_json
    assert "docker" in ctx.env_json["python"]["env_types"]
    assert "test" in ctx.env_json["python"]["commands"]
    assert ctx.contest_current_path == "./contest_current"


def test_parse_python_alias():
    args = ["py", "local", "t", "abc300", "a"]
    operations = build_mock_operations()
    file_driver = inject_env_json_to_operations(operations)
    print(f"[DEBUG] test_parse_python_alias: id(file_driver)={id(file_driver)}")
    print(f"[DEBUG] test_parse_python_alias: id(operations.resolve('file_driver'))={id(operations.resolve('file_driver'))}")
    print(f"[DEBUG] test_parse_python_alias: args={args}")
    print(f"[DEBUG] test_parse_python_alias: file_driver.files={file_driver.files}")
    print(f"[DEBUG] test_parse_python_alias: env_json={file_driver.contents}")
    from src.context.user_input_parser import _load_all_env_jsons, CONTEST_ENV_DIR
    env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR, operations)
    merged_env_json = {}
    for env_json in env_jsons:
        merged_env_json.update(env_json)
    print(f"[DEBUG] test_parse_python_alias: merged_env_json={merged_env_json}")
    ctx = parse_user_input(args, operations)
    assert ctx.language == "python"
    assert ctx.env_type == "local"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"
    assert ctx.env_json is not None
    assert "python" in ctx.env_json
    assert "local" in ctx.env_json["python"]["env_types"]
    assert "test" in ctx.env_json["python"]["commands"]
    assert ctx.contest_current_path == "./contest_current"


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
    assert "以下の項目が指定されていません: 言語" in str(e.value)


def test_env_json_load():
    operations = build_mock_operations()
    file_driver = inject_env_json_to_operations(operations)
    py_path = file_driver.base_dir / "contest_env/python/env.json"
    rs_path = file_driver.base_dir / "contest_env/rust/env.json"
    print(f"[DEBUG] base_dir: {file_driver.base_dir}")
    print(f"[DEBUG] py_path: {py_path}")
    print(f"[DEBUG] file_driver.files: {file_driver.files}")
    # ファイルが存在するか（Path型で判定）
    assert py_path in file_driver.files
    assert rs_path in file_driver.files
    # 内容が正しいか
    import json as _json
    py_data = _json.loads(file_driver.contents[py_path])
    rs_data = _json.loads(file_driver.contents[rs_path])
    assert py_data["python"]["contest_current_path"] == "./contest_current"
    assert rs_data["rust"]["contest_current_path"] == "./contest_current"