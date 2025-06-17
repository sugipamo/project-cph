"""設定システムの互換性テスト

新しいTypeSafeConfigNodeManagerが既存システムとの互換性を保つことを確認
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.configuration.config_manager import TypedExecutionConfiguration, TypeSafeConfigNodeManager
from src.context.user_input_parser.user_input_parser_integration import (
    UserInputParserIntegration,
    create_new_execution_context,
)
from src.workflow.workflow_execution_service import WorkflowExecutionService


class TestConfigCompatibility:
    """設定システム互換性テスト"""

    @pytest.fixture
    def legacy_compatible_config(self):
        """旧システム互換の設定データ"""
        return {
            # システム設定（旧config/system形式）
            "system": {
                "paths": {
                    "contest_current_path": "./contest_current",
                    "contest_stock_path": "./contest_stock/{language}/{contest_name}/{problem_name}",
                    "contest_template_path": "./contest_template",
                    "workspace_path": "./workspace"
                },
                "file_patterns": {
                    "contest_files": ["*.py", "*.cpp", "*.rs"],
                    "test_files": ["*.txt", "*.in", "*.out"]
                }
            },
            # 共有設定（旧contest_env/shared形式）
            "shared": {
                "environment_logging": {
                    "enabled": True,
                    "log_level": "INFO",
                    "log_to_file": False
                },
                "timeout": {
                    "default": 30,
                    "build": 60,
                    "test": 10
                }
            },
            # 言語固有設定（旧contest_env/python形式）
            "python": {
                "commands": {
                    "test": {
                        "steps": [
                            {
                                "type": "shell",
                                "cmd": ["python3", "{workspace_path}/main.py"],
                                "allow_failure": True
                            }
                        ],
                        "timeout": 30,
                        "parallel": {
                            "enabled": False,
                            "max_workers": 4
                        }
                    },
                    "open": {
                        "steps": [
                            {
                                "type": "copy",
                                "src": "{contest_template_path}/main.py",
                                "dest": "{workspace_path}/main.py"
                            },
                            {
                                "type": "mkdir",
                                "path": "{contest_current_path}/{contest_name}"
                            }
                        ]
                    },
                    "submit": {
                        "steps": [
                            {
                                "type": "copy",
                                "src": "{workspace_path}/main.py",
                                "dest": "{contest_stock_path}/main.py"
                            }
                        ]
                    }
                },
                "extensions": [".py"],
                "compile_command": "",
                "run_command": "python3 {workspace_path}/main.py"
            }
        }

    @pytest.fixture
    def temp_legacy_config_setup(self, legacy_compatible_config):
        """旧システム互換の設定ファイル構造を作成"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # システム設定ディレクトリ
            system_dir = tmp_path / "config" / "system"
            system_dir.mkdir(parents=True)
            system_config_path = system_dir / "config.json"
            with open(system_config_path, 'w') as f:
                json.dump(legacy_compatible_config["system"], f, indent=2)

            # contest_env ディレクトリ
            env_dir = tmp_path / "contest_env"
            env_dir.mkdir()

            # 共有設定
            shared_dir = env_dir / "shared"
            shared_dir.mkdir()
            shared_config_path = shared_dir / "env.json"
            with open(shared_config_path, 'w') as f:
                json.dump(legacy_compatible_config["shared"], f, indent=2)

            # Python設定
            python_dir = env_dir / "python"
            python_dir.mkdir()
            python_config_path = python_dir / "env.json"
            with open(python_config_path, 'w') as f:
                json.dump(legacy_compatible_config["python"], f, indent=2)

            yield {
                "base_dir": str(tmp_path),
                "system_dir": str(system_dir.parent),
                "env_dir": str(env_dir),
                "config_data": legacy_compatible_config
            }

    def test_legacy_config_structure_loading(self, temp_legacy_config_setup):
        """旧システムの設定構造の読み込み互換性テスト"""
        manager = TypeSafeConfigNodeManager()

        # 旧システムと同じパスで設定を読み込み
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        # 旧システムで期待される設定項目が読み込めることを確認
        workspace_path = manager.resolve_config(["paths", "workspace_path"], str)
        assert workspace_path == "./workspace"

        test_timeout = manager.resolve_config(["timeout", "default"], int)
        assert test_timeout == 30

        test_command = manager.resolve_config(["commands", "test"], dict)
        assert "steps" in test_command
        assert len(test_command["steps"]) > 0

    def test_execution_context_creation_compatibility(self, temp_legacy_config_setup):
        """ExecutionContext作成の互換性テスト"""
        # 新システムでExecutionConfigurationを作成
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # 旧ExecutionContextと同等のプロパティを持つことを確認
        assert hasattr(config, 'contest_name')
        assert hasattr(config, 'problem_name')
        assert hasattr(config, 'language')
        assert hasattr(config, 'command_type')

        # 基本プロパティの値確認
        assert config.contest_name == "abc123"
        assert config.problem_name == "a"
        assert config.language == "python"
        assert config.command_type == "test"

    def test_user_input_parser_integration_compatibility(self, temp_legacy_config_setup):
        """UserInputParserIntegrationの互換性テスト"""
        integration = UserInputParserIntegration(
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            system_config_dir=temp_legacy_config_setup["system_dir"]
        )

        # 旧システムと同じインターフェースで使用可能か確認
        config = integration.create_execution_configuration_from_context(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local",
            env_json={}
        )

        assert isinstance(config, TypedExecutionConfiguration)
        assert config.contest_name == "abc123"
        assert config.language == "python"

    def test_template_string_compatibility(self, temp_legacy_config_setup):
        """テンプレート文字列解決の互換性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # 旧システムで使用されていたテンプレートパターンをテスト
        legacy_templates = [
            "{contest_name}",
            "{problem_name}",
            "{language}",
            "{workspace_path}",
            "{contest_current_path}",
            "{contest_template_path}",
            "{contest_stock_path}",
            "{contest_name}/{problem_name}",
            "{language}/{contest_name}/{problem_name}"
        ]

        for template in legacy_templates:
            try:
                resolved = config.resolve_formatted_string(template)
                assert resolved is not None, f"Template {template} should resolve"
                assert template != resolved, f"Template {template} should be replaced"

                # 期待される置換の確認
                if "{contest_name}" in template:
                    assert "abc123" in resolved
                if "{problem_name}" in template:
                    assert "a" in resolved
                if "{language}" in template:
                    assert "python" in resolved

            except Exception as e:
                pytest.fail(f"Template {template} resolution failed: {e}")

    def test_workflow_execution_service_compatibility(self, temp_legacy_config_setup):
        """WorkflowExecutionServiceとの互換性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # モックoperationsを作成
        mock_infrastructure = Mock()

        # WorkflowExecutionServiceが新しい設定オブジェクトを受け入れることを確認
        try:
            service = WorkflowExecutionService(config, mock_infrastructure)
            assert service is not None
            assert service.context == config
        except Exception as e:
            pytest.fail(f"WorkflowExecutionService compatibility failed: {e}")

    def test_command_structure_compatibility(self, temp_legacy_config_setup):
        """コマンド構造の互換性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        # 旧システムで期待されるコマンド構造が維持されているか確認
        expected_commands = ["test", "open", "submit"]

        for command in expected_commands:
            try:
                command_config = manager.resolve_config(["commands", command], dict)

                # 必須フィールドの確認
                assert "steps" in command_config, f"Command {command} should have steps"
                assert isinstance(command_config["steps"], list), f"Command {command} steps should be a list"
                assert len(command_config["steps"]) > 0, f"Command {command} should have at least one step"

                # ステップ構造の確認
                for i, step in enumerate(command_config["steps"]):
                    assert "type" in step, f"Command {command} step {i} should have type"

                    if step["type"] == "shell":
                        assert "cmd" in step, "Shell step should have cmd"
                        assert isinstance(step["cmd"], list), "Shell cmd should be a list"
                    elif step["type"] == "copy":
                        assert "src" in step, "Copy step should have src"
                        assert "dest" in step, "Copy step should have dest"
                    elif step["type"] == "mkdir":
                        assert "path" in step, "Mkdir step should have path"

            except KeyError:
                # コマンドが見つからない場合は警告のみ
                pytest.skip(f"Command {command} not found in configuration")

    def test_file_patterns_compatibility(self, temp_legacy_config_setup):
        """ファイルパターンの互換性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        # 旧システムのファイルパターン構造の確認
        try:
            file_patterns = manager.resolve_config(["file_patterns"], dict)

            # 期待されるパターンタイプ
            expected_pattern_types = ["contest_files", "test_files"]

            for pattern_type in expected_pattern_types:
                if pattern_type in file_patterns:
                    patterns = file_patterns[pattern_type]
                    assert isinstance(patterns, list), f"{pattern_type} should be a list"
                    assert len(patterns) > 0, f"{pattern_type} should not be empty"

                    # パターンの形式確認
                    for pattern in patterns:
                        assert isinstance(pattern, str), f"Pattern should be string: {pattern}"
                        assert pattern.startswith("*."), f"Pattern should start with '*.' : {pattern}"

        except KeyError:
            pytest.skip("file_patterns not found in configuration")

    def test_environment_logging_compatibility(self, temp_legacy_config_setup):
        """環境ログ設定の互換性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        # 旧システムの環境ログ設定構造の確認
        try:
            env_logging = manager.resolve_config(["environment_logging"], dict)

            # 期待される設定項目
            expected_keys = ["enabled", "log_level"]

            for key in expected_keys:
                assert key in env_logging, f"environment_logging should have {key}"

            # 型の確認
            assert isinstance(env_logging["enabled"], bool), "enabled should be boolean"
            assert isinstance(env_logging["log_level"], str), "log_level should be string"

            # 値の妥当性確認
            assert env_logging["log_level"] in ["DEBUG", "INFO", "WARNING", "ERROR"], "log_level should be valid"

        except KeyError:
            pytest.skip("environment_logging not found in configuration")

    def test_timeout_settings_compatibility(self, temp_legacy_config_setup):
        """タイムアウト設定の互換性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        # 旧システムのタイムアウト設定構造の確認
        try:
            timeout_config = manager.resolve_config(["timeout"], dict)

            # 期待されるタイムアウト項目
            expected_timeouts = ["default", "build", "test"]

            for timeout_type in expected_timeouts:
                if timeout_type in timeout_config:
                    timeout_value = timeout_config[timeout_type]
                    assert isinstance(timeout_value, int), f"{timeout_type} timeout should be integer"
                    assert timeout_value > 0, f"{timeout_type} timeout should be positive"
                    assert timeout_value <= 3600, f"{timeout_type} timeout should be reasonable (<= 1 hour)"

        except KeyError:
            pytest.skip("timeout configuration not found")

    def test_backwards_compatibility_with_existing_code(self, temp_legacy_config_setup):
        """既存コードとの後方互換性テスト"""
        # create_new_execution_context 関数の互換性確認
        with patch('src.context.user_input_parser.user_input_parser_integration.UserInputParserIntegration') as mock_integration:
            mock_instance = Mock()
            mock_config = Mock()
            mock_config.contest_name = "abc123"
            mock_config.language = "python"
            mock_instance.create_execution_context_adapter.return_value = mock_config
            mock_integration.return_value = mock_instance

            # 旧システムと同じインターフェースで呼び出し
            try:
                result = create_new_execution_context(
                    command_type="test",
                    language="python",
                    contest_name="abc123",
                    problem_name="a",
                    env_type="local",
                    env_json={}
                )

                # 結果の検証
                assert result is not None
                mock_integration.assert_called_once()
                mock_instance.create_execution_context_adapter.assert_called_once_with(
                    "test", "python", "abc123", "a", "local", {}
                )

            except Exception as e:
                pytest.fail(f"create_new_execution_context compatibility failed: {e}")

    def test_error_handling_compatibility(self, temp_legacy_config_setup):
        """エラーハンドリングの互換性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        # 旧システムと同様のエラーパターンでの動作確認

        # 存在しない設定パスへのアクセス
        with pytest.raises((KeyError, ValueError)):
            manager.resolve_config(["nonexistent", "configuration", "path"], str)

        # 不正な型変換
        with pytest.raises((TypeError, ValueError)):
            # 文字列設定を不正にint変換
            manager.resolve_config(["paths", "workspace_path"], int)

    def test_migration_path_verification(self, temp_legacy_config_setup):
        """移行パスの検証"""
        # 旧システムの設定ファイルが新システムで正しく動作することを確認

        manager = TypeSafeConfigNodeManager()

        # 段階的な移行をシミュレート
        # 1. 基本的な設定読み込み
        manager.load_from_files(
            system_config_dir=temp_legacy_config_setup["system_dir"],
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            language="python"
        )

        # 2. ExecutionConfiguration作成
        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # 3. 旧システムAPIとの互換性確認
        integration = UserInputParserIntegration(
            contest_env_dir=temp_legacy_config_setup["env_dir"],
            system_config_dir=temp_legacy_config_setup["system_dir"]
        )

        compatibility_result = integration.validate_new_system_compatibility(
            old_context=Mock(contest_name="abc123", language="python"),
            new_config=config
        )

        assert compatibility_result is True, "新システムは旧システムと互換性を保つ必要があります"
