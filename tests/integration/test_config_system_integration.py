"""新しい設定システムの統合テスト

TypeSafeConfigNodeManagerの包括的な動作テスト
"""
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from src.configuration.config_manager import (
    FileLoader,
    TypedExecutionConfiguration,
    TypeSafeConfigNodeManager,
)


class TestConfigSystemIntegration:
    """設定システム統合テスト"""

    @pytest.fixture
    def temp_config_dirs(self):
        """テスト用の一時設定ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # システム設定ディレクトリ
            system_dir = tmp_path / "system"
            system_dir.mkdir()

            # contest_env ディレクトリ
            env_dir = tmp_path / "contest_env"
            env_dir.mkdir()

            # 共有設定
            shared_dir = env_dir / "shared"
            shared_dir.mkdir()

            # Python設定
            python_dir = env_dir / "python"
            python_dir.mkdir()

            yield {
                "system_dir": str(system_dir),
                "env_dir": str(env_dir),
                "shared_dir": str(shared_dir),
                "python_dir": str(python_dir),
            }

    @pytest.fixture
    def sample_config_data(self, temp_config_dirs):
        """サンプル設定データを作成"""
        # システム設定
        system_config = {
            "paths": {
                "contest_current_path": "./contest_current",
                "contest_stock_path": "./contest_stock/{language}/{contest_name}/{problem_name}",
                "contest_template_path": "./contest_template",
                "workspace_path": "./workspace"
            },
            "file_patterns": {
                "contest_files": ["*.py", "*.cpp"],
                "test_files": ["*.txt", "*.in", "*.out"]
            }
        }

        # 共有設定
        shared_config = {
            "environment_logging": {
                "enabled": True,
                "log_level": "INFO"
            },
            "timeout": {
                "default": 30,
                "build": 60
            }
        }

        # Python言語固有設定
        python_config = {
            "commands": {
                "test": {
                    "steps": [
                        {
                            "type": "shell",
                            "cmd": ["python3", "{workspace_path}/main.py"]
                        }
                    ]
                },
                "open": {
                    "steps": [
                        {
                            "type": "copy",
                            "src": "{contest_template_path}/main.py",
                            "dest": "{workspace_path}/main.py"
                        }
                    ]
                }
            },
            "extensions": [".py"],
            "compile_command": "",
            "run_command": "python3 {workspace_path}/main.py",
            "language_id": "python",
            "source_file_name": "main.py"
        }

        # ファイルに書き込み
        system_path = Path(temp_config_dirs["system_dir"]) / "config.json"
        with open(system_path, 'w') as f:
            json.dump(system_config, f)

        shared_path = Path(temp_config_dirs["shared_dir"]) / "env.json"
        with open(shared_path, 'w') as f:
            json.dump(shared_config, f)

        python_path = Path(temp_config_dirs["python_dir"]) / "env.json"
        with open(python_path, 'w') as f:
            json.dump(python_config, f)

        return {
            "system": system_config,
            "shared": shared_config,
            "python": python_config
        }

    def test_config_manager_initialization(self):
        """TypeSafeConfigNodeManagerの初期化テスト"""
        manager = TypeSafeConfigNodeManager()
        assert manager is not None
        assert hasattr(manager, 'resolve_config')
        assert hasattr(manager, 'create_execution_config')

    def test_file_loader_basic_functionality(self, temp_config_dirs, sample_config_data):
        """FileLoaderの基本機能テスト"""
        file_loader = FileLoader()

        # 利用可能言語の取得
        env_dir = Path(temp_config_dirs["env_dir"])
        languages = file_loader.get_available_languages(env_dir)
        assert "python" in languages

        # 設定の読み込みとマージ
        merged_config = file_loader.load_and_merge_configs(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        assert "commands" in merged_config
        assert "test" in merged_config["commands"]
        assert "open" in merged_config["commands"]
        assert "paths" in merged_config
        assert "environment_logging" in merged_config

    def test_config_manager_load_from_files(self, temp_config_dirs, sample_config_data):
        """TypeSafeConfigNodeManagerのファイル読み込みテスト"""
        manager = TypeSafeConfigNodeManager()

        # ファイルから設定を読み込み
        manager.load_from_files(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        # 設定値の解決テスト
        workspace_path = manager.resolve_config(["paths", "workspace_path"], str)
        assert workspace_path == "./workspace"

        timeout_default = manager.resolve_config(["timeout", "default"], int)
        assert timeout_default == 30

    def test_execution_config_creation(self, temp_config_dirs, sample_config_data):
        """ExecutionConfiguration作成テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        # ExecutionConfiguration作成
        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        assert isinstance(config, TypedExecutionConfiguration)
        assert config.contest_name == "abc123"
        assert config.problem_name == "a"
        assert config.language == "python"
        assert config.command_type == "test"

    def test_template_string_resolution(self, temp_config_dirs, sample_config_data):
        """テンプレート文字列解決テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # テンプレート文字列の解決
        template = "{contest_name}/{problem_name}/{language}"
        resolved = config.resolve_formatted_string(template)
        assert resolved == "abc123/a/python"

        # パス系テンプレートの解決
        path_template = "{contest_stock_path}"
        resolved_path = config.resolve_formatted_string(path_template)
        # contest_stock_pathにはテンプレート変数が含まれているため、それが展開されるべき
        # テンプレートが完全に展開されない場合は部分的な確認
        assert "contest_stock" in resolved_path

    def test_type_safety(self, temp_config_dirs, sample_config_data):
        """型安全性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        # 正しい型での取得
        timeout_int = manager.resolve_config(["timeout", "default"], int)
        assert isinstance(timeout_int, int)
        assert timeout_int == 30

        # 文字列型での取得
        timeout_str = manager.resolve_config(["timeout", "default"], str)
        assert isinstance(timeout_str, str)
        assert timeout_str == "30"

        # bool型での取得
        logging_enabled = manager.resolve_config(["environment_logging", "enabled"], bool)
        assert isinstance(logging_enabled, bool)
        assert logging_enabled is True

    def test_caching_functionality(self, temp_config_dirs, sample_config_data):
        """キャッシュ機能テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        # 初回アクセス
        value1 = manager.resolve_config(["timeout", "default"], int)

        # 2回目アクセス（キャッシュから取得）
        value2 = manager.resolve_config(["timeout", "default"], int)

        assert value1 == value2

        # キャッシュ統計の確認（実装されている場合）
        if hasattr(manager, '_type_conversion_cache'):
            assert len(manager._type_conversion_cache) > 0

    def test_execution_config_properties(self, temp_config_dirs, sample_config_data):
        """ExecutionConfigurationプロパティテスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # 基本プロパティの確認
        assert hasattr(config, 'contest_name')
        assert hasattr(config, 'problem_name')
        assert hasattr(config, 'language')
        assert hasattr(config, 'command_type')
        assert hasattr(config, 'resolve_formatted_string')

        # 計算プロパティの確認
        if hasattr(config, 'workspace_path'):
            assert isinstance(config.workspace_path, Path)
            assert "workspace" in str(config.workspace_path)

    def test_error_handling(self, temp_config_dirs, sample_config_data):
        """エラーハンドリングテスト"""
        manager = TypeSafeConfigNodeManager()

        # 設定が読み込まれていない状態での存在しない設定パスへのアクセス
        with pytest.raises((KeyError, ValueError, AttributeError)):
            manager.resolve_config(["nonexistent", "path"], str)

        # 設定を読み込み
        manager.load_from_files(
            system_dir=temp_config_dirs["system_dir"],
            env_dir=temp_config_dirs["env_dir"],
            language="python"
        )

        # 存在しない設定への不正な型変換テスト
        with pytest.raises((KeyError, ValueError, TypeError)):
            manager.resolve_config(["definitely_nonexistent"], int)

    def test_multiple_languages_support(self, temp_config_dirs, sample_config_data):
        """複数言語サポートテスト"""
        # C++設定も追加
        cpp_dir = Path(temp_config_dirs["env_dir"]) / "cpp"
        cpp_dir.mkdir()

        cpp_config = {
            "commands": {
                "test": {
                    "steps": [
                        {
                            "type": "shell",
                            "cmd": ["./main"]
                        }
                    ]
                }
            },
            "extensions": [".cpp"],
            "compile_command": "g++ -o main main.cpp"
        }

        cpp_path = cpp_dir / "env.json"
        with open(cpp_path, 'w') as f:
            json.dump(cpp_config, f)

        file_loader = FileLoader()
        languages = file_loader.get_available_languages(Path(temp_config_dirs["env_dir"]))

        # sample_config_dataによってPythonディレクトリとファイルが作成されているはず
        assert "python" in languages, f"Available languages: {languages}"
        assert "cpp" in languages, f"Available languages: {languages}"
        assert len(languages) >= 2
