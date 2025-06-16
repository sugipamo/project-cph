"""PureSettingsManager の単体テスト

3層純化設定システムのテスト
"""
from unittest.mock import MagicMock, Mock

import pytest

from src.configuration.services.pure_settings_manager import (
    PureExecutionSettings,
    PureRuntimeSettings,
    PureSettingsManager,
)
from tests.configuration.test_fixtures_separated_system import (
    mock_execution_settings,
    mock_runtime_settings,
    sample_template_context,
)


class TestPureExecutionSettings:
    """PureExecutionSettingsの単体テスト"""

    def test_initialization(self):
        """初期化テスト"""
        # Act
        settings = PureExecutionSettings(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open"
        )

        # Assert
        assert settings.get_contest_name() == "abc300"
        assert settings.get_problem_name() == "a"
        assert settings.get_language() == "python"
        assert settings.get_env_type() == "local"
        assert settings.get_command_type() == "open"

    def test_initialization_with_optional_parameters(self):
        """オプションパラメーター付き初期化テスト"""
        # Arrange
        paths = {"contest_current_path": "./contest_current"}
        file_patterns = {"contest_files": ["*.py"]}

        # Act
        settings = PureExecutionSettings(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open",
            old_contest_name="abc299",
            old_problem_name="b",
            paths=paths,
            file_patterns=file_patterns
        )

        # Assert
        assert settings.get_old_contest_name() == "abc299"
        assert settings.get_old_problem_name() == "b"
        assert settings.get_paths() == paths
        assert settings.get_file_patterns() == file_patterns

    def test_to_template_dict(self):
        """テンプレート辞書生成テスト"""
        # Arrange
        paths = {
            "contest_current_path": "./contest_current",
            "workspace": "./workspace"
        }

        settings = PureExecutionSettings(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open",
            old_contest_name="abc299",
            old_problem_name="b",
            paths=paths
        )

        # Act
        result = settings.to_template_dict()

        # Assert
        expected_keys = {
            "contest_name", "problem_name", "old_contest_name", "old_problem_name",
            "language", "language_name", "env_type", "command_type",
            "contest_current_path", "workspace", "workspace_path"
        }
        assert set(result.keys()) == expected_keys
        assert result["contest_name"] == "abc300"
        assert result["language"] == result["language_name"]  # エイリアス確認
        assert result["workspace"] == result["workspace_path"]  # _pathサフィックス確認

    def test_get_paths_returns_copy(self):
        """パス取得で元データが変更されないことのテスト"""
        # Arrange
        original_paths = {"test_path": "./test"}
        settings = PureExecutionSettings(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open",
            paths=original_paths
        )

        # Act
        returned_paths = settings.get_paths()
        returned_paths["modified"] = "./modified"

        # Assert
        assert "modified" not in settings.get_paths()
        assert settings.get_paths() == original_paths


class TestPureRuntimeSettings:
    """PureRuntimeSettingsの単体テスト"""

    def test_initialization(self):
        """初期化テスト"""
        # Act
        settings = PureRuntimeSettings(
            language_id="4006",
            source_file_name="main.py",
            run_command="python3"
        )

        # Assert
        assert settings.get_language_id() == "4006"
        assert settings.get_source_file_name() == "main.py"
        assert settings.get_run_command() == "python3"
        assert settings.get_timeout_seconds() == 300  # デフォルト値
        assert settings.get_retry_settings() == {}  # デフォルト値

    def test_initialization_with_optional_parameters(self):
        """オプションパラメーター付き初期化テスト"""
        # Arrange
        retry_settings = {"max_attempts": 3, "delay": 1.0}

        # Act
        settings = PureRuntimeSettings(
            language_id="4003",
            source_file_name="main.cpp",
            run_command="g++ -o main main.cpp && ./main",
            timeout_seconds=600,
            retry_settings=retry_settings
        )

        # Assert
        assert settings.get_timeout_seconds() == 600
        assert settings.get_retry_settings() == retry_settings

    def test_to_runtime_dict(self):
        """Runtime辞書生成テスト"""
        # Arrange
        settings = PureRuntimeSettings(
            language_id="4006",
            source_file_name="main.py",
            run_command="python3",
            timeout_seconds=300
        )

        # Act
        result = settings.to_runtime_dict()

        # Assert
        expected = {
            "language_id": "4006",
            "source_file_name": "main.py",
            "run_command": "python3",
            "timeout_seconds": "300"  # 文字列変換確認
        }
        assert result == expected

    def test_get_retry_settings_returns_copy(self):
        """リトライ設定取得で元データが変更されないことのテスト"""
        # Arrange
        original_retry = {"max_attempts": 3}
        settings = PureRuntimeSettings(
            language_id="4006",
            source_file_name="main.py",
            run_command="python3",
            retry_settings=original_retry
        )

        # Act
        returned_retry = settings.get_retry_settings()
        returned_retry["modified"] = True

        # Assert
        assert "modified" not in settings.get_retry_settings()
        assert settings.get_retry_settings() == original_retry


class TestPureSettingsManager:
    """PureSettingsManagerの単体テスト"""

    @pytest.fixture
    def mock_config_loader(self):
        """ConfigurationLoaderのモック"""
        mock_loader = Mock()
        mock_config_source = Mock()
        mock_config_source.get_paths.return_value = {
            "contest_current_path": "./contest_current",
            "contest_stock_path": "./contest_stock/{language}/{contest}/{problem}"
        }
        mock_config_source.get_file_patterns.return_value = {
            "contest_files": ["*.py"],
            "test_files": ["*.txt"]
        }
        mock_loader.load_configuration.return_value = mock_config_source
        return mock_loader

    @pytest.fixture
    def mock_language_registry(self):
        """LanguageRegistryのモック"""
        mock_registry = Mock()
        mock_registry.get_language_config.return_value = {
            "language_id": "4006",
            "source_file_name": "main.py",
            "run_command": "python3",
            "timeout_seconds": 300,
            "retry_settings": {"max_attempts": 3}
        }
        return mock_registry

    @pytest.fixture
    def settings_manager(self, mock_config_loader, mock_language_registry):
        """PureSettingsManagerのインスタンス"""
        return PureSettingsManager(mock_config_loader, mock_language_registry)

    def test_initialization_required(self, settings_manager):
        """初期化前の実行設定取得でエラーが発生することのテスト"""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Execution settings not initialized"):
            settings_manager.get_execution_settings()

    def test_initialize_and_get_execution_settings(self, settings_manager, mock_config_loader):
        """初期化と実行設定取得テスト"""
        # Act
        settings_manager.initialize(
            contest_name="abc300",
            problem_name="a",
            language="python"
        )

        # Assert
        mock_config_loader.load_configuration.assert_called_once_with(
            language="python",
            env_type="local"
        )

        execution_settings = settings_manager.get_execution_settings()
        assert execution_settings.get_contest_name() == "abc300"
        assert execution_settings.get_problem_name() == "a"
        assert execution_settings.get_language() == "python"

    def test_get_runtime_settings(self, settings_manager, mock_language_registry):
        """Runtime設定取得テスト"""
        # Act
        runtime_settings = settings_manager.get_runtime_settings("python")

        # Assert
        mock_language_registry.get_language_config.assert_called_with("python")
        assert runtime_settings.get_language_id() == "4006"
        assert runtime_settings.get_source_file_name() == "main.py"
        assert runtime_settings.get_run_command() == "python3"

    def test_expand_template(self, settings_manager):
        """テンプレート展開テスト"""
        # Arrange
        template = "Contest: {contest_name}, Problem: {problem_name}"
        context = {"contest_name": "abc300", "problem_name": "a"}

        # Act
        result = settings_manager.expand_template(template, context)

        # Assert
        assert result == "Contest: abc300, Problem: a"

    def test_expand_template_missing_variables(self, settings_manager):
        """未定義変数があるテンプレート展開テスト"""
        # Arrange
        template = "Contest: {contest_name}, Problem: {unknown_var}"
        context = {"contest_name": "abc300"}

        # Act
        result = settings_manager.expand_template(template, context)

        # Assert
        assert result == "Contest: abc300, Problem: {unknown_var}"

    def test_save_and_load_execution_context(self, settings_manager):
        """実行コンテキストの保存・読み込みテスト（責務外）"""
        # Arrange
        context = {"test": "data"}

        # Act & Assert - 設定システムでは状態管理は責務外
        settings_manager.save_execution_context(context)  # 例外が発生しないことを確認
        result = settings_manager.load_execution_context()
        assert result == {}  # 空の辞書が返される
