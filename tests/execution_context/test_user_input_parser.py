import os
import shutil
import tempfile
import json
import pytest
from src.context.user_input_parser import UserInputParser, SystemInfoProvider
from src.context.execution_context import ExecutionContext

# テスト用のSystemInfoProviderモック
class DummySystemInfoProvider(SystemInfoProvider):
    def __init__(self, info=None):
        self._info = info or {
            "command": None,
            "language": None,
            "env_type": None,
            "contest_name": None,
            "problem_name": None,
            "contest_current_path": None,
            "env_json": None
        }
        self.saved = None
    def load(self):
        return self._info
    def save(self, info):
        self.saved = info

@pytest.fixture(scope="module")
def setup_env(tmp_path_factory):
    # contest_envディレクトリを一時ディレクトリにコピー
    tmp_dir = tmp_path_factory.mktemp("contest_env")
    shutil.copytree("contest_env/python", tmp_dir / "python")
    shutil.copytree("contest_env/rust", tmp_dir / "rust")
    return str(tmp_dir)

@pytest.mark.usefixtures("setup_env")
def test_parse_python_command(monkeypatch, setup_env):
    # contest_envのパスを一時ディレクトリに差し替え
    monkeypatch.setattr("src.context.user_input_parser.CONTEST_ENV_DIR", setup_env)
    provider = DummySystemInfoProvider()
    parser = UserInputParser(system_info_provider=provider)
    args = ["python", "docker", "test", "abc300", "a"]
    ctx = parser.parse_and_validate(args)
    assert ctx.language == "python"
    assert ctx.env_type == "docker"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"
    assert ctx.env_json is not None
    assert "python" in ctx.env_json
    assert ctx.contest_current_path == "./contest_current"
    # system_info.jsonへの保存内容も確認
    assert provider.saved["language"] == "python"
    assert provider.saved["command"] == "test"

@pytest.mark.usefixtures("setup_env")
def test_parse_python_alias(monkeypatch, setup_env):
    monkeypatch.setattr("src.context.user_input_parser.CONTEST_ENV_DIR", setup_env)
    provider = DummySystemInfoProvider()
    parser = UserInputParser(system_info_provider=provider)
    args = ["py", "local", "t", "abc300", "a"]
    ctx = parser.parse_and_validate(args)
    assert ctx.language == "python"
    assert ctx.env_type == "local"
    assert ctx.command_type == "test"
    assert ctx.problem_name == "a"
    assert ctx.contest_name == "abc300"

@pytest.mark.usefixtures("setup_env")
def test_parse_too_many_args(monkeypatch, setup_env):
    monkeypatch.setattr("src.context.user_input_parser.CONTEST_ENV_DIR", setup_env)
    provider = DummySystemInfoProvider()
    parser = UserInputParser(system_info_provider=provider)
    args = ["python", "docker", "test", "abc300", "a", "extra"]
    with pytest.raises(ValueError) as e:
        parser.parse_and_validate(args)
    assert "引数が多すぎます" in str(e.value)

@pytest.mark.usefixtures("setup_env")
def test_parse_missing_required(monkeypatch, setup_env):
    monkeypatch.setattr("src.context.user_input_parser.CONTEST_ENV_DIR", setup_env)
    provider = DummySystemInfoProvider()
    parser = UserInputParser(system_info_provider=provider)
    # 言語指定なし
    args = ["docker", "test", "abc300", "a"]
    with pytest.raises(ValueError) as e:
        parser.parse_and_validate(args)
    assert "引数が多すぎます" in str(e.value) 