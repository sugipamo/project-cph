"""UnifiedExecutionAdapter の単体テスト

統一実行アダプターの互換性テスト
"""
from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from src.configuration.adapters.unified_execution_adapter import UnifiedExecutionAdapter
from src.state.interfaces.state_manager import ExecutionHistory, SessionContext
from tests.configuration.test_fixtures_separated_system import (
    mock_settings_manager,
    mock_state_manager,
    sample_execution_history,
    sample_session_context,
)


class TestUnifiedExecutionAdapter:
    """UnifiedExecutionAdapterの単体テスト"""

    @pytest.fixture
    def mock_settings_manager_with_init(self):
        """初期化可能なSettingsManagerのモック"""
        mock_manager = Mock()
        mock_manager.initialize = Mock()

        # ExecutionSettings のモック
        mock_execution_settings = Mock()
        mock_execution_settings.get_contest_name.return_value = "abc300"
        mock_execution_settings.get_problem_name.return_value = "a"
        mock_execution_settings.get_language.return_value = "python"
        mock_execution_settings.get_env_type.return_value = "local"
        mock_execution_settings.get_command_type.return_value = "open"
        mock_execution_settings.get_old_contest_name.return_value = "abc299"
        mock_execution_settings.get_old_problem_name.return_value = "b"
        mock_execution_settings.to_template_dict.return_value = {
            "contest_name": "abc300",
            "problem_name": "a",
            "language": "python",
            "env_type": "local"
        }

        # RuntimeSettings のモック
        mock_runtime_settings = Mock()
        mock_runtime_settings.to_runtime_dict.return_value = {
            "language_id": "4006",
            "source_file_name": "main.py",
            "run_command": "python3"
        }

        mock_manager.get_execution_settings.return_value = mock_execution_settings
        mock_manager.get_runtime_settings.return_value = mock_runtime_settings
        mock_manager.expand_template.side_effect = lambda template, context: template.format(**context)

        return mock_manager

    @pytest.fixture
    def mock_state_manager_with_context(self):
        """セッションコンテキスト付きStateManagerのモック"""
        mock_manager = Mock()
        mock_manager.save_session_context = Mock()
        mock_manager.save_execution_history = Mock()
        mock_manager.get_execution_history.return_value = []

        # 前回のセッションコンテキスト
        previous_context = SessionContext(
            current_contest="abc299",
            current_problem="b",
            current_language="python",
            previous_contest="abc298",
            previous_problem="a",
            user_specified_fields={}
        )
        mock_manager.load_session_context.return_value = previous_context

        return mock_manager

    @pytest.fixture
    def adapter(self, mock_settings_manager_with_init, mock_state_manager_with_context):
        """UnifiedExecutionAdapterのインスタンス"""
        return UnifiedExecutionAdapter(
            mock_settings_manager_with_init,
            mock_state_manager_with_context
        )

    def test_initialization(self, adapter, mock_settings_manager_with_init, mock_state_manager_with_context):
        """アダプターの初期化テスト"""
        # Act
        adapter.initialize(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open"
        )

        # Assert
        # 設定マネージャーの初期化が呼ばれることを確認
        mock_settings_manager_with_init.initialize.assert_called_once_with(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open",
            old_contest_name="abc299",  # 前回のコンテスト名
            old_problem_name="b"        # 前回の問題名
        )

        # 新しいセッションコンテキストの保存が呼ばれることを確認
        mock_state_manager_with_context.save_session_context.assert_called_once()
        saved_context = mock_state_manager_with_context.save_session_context.call_args[0][0]
        assert saved_context.current_contest == "abc300"
        assert saved_context.current_problem == "a"
        assert saved_context.previous_contest == "abc299"
        assert saved_context.previous_problem == "b"

    def test_initialization_without_previous_context(self, mock_settings_manager_with_init):
        """前回のセッションがない場合の初期化テスト"""
        # Arrange
        mock_state_manager = Mock()
        mock_state_manager.load_session_context.return_value = None
        mock_state_manager.save_session_context = Mock()

        adapter = UnifiedExecutionAdapter(
            mock_settings_manager_with_init,
            mock_state_manager
        )

        # Act
        adapter.initialize(
            contest_name="abc300",
            problem_name="a",
            language="python"
        )

        # Assert
        mock_settings_manager_with_init.initialize.assert_called_once_with(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open",
            old_contest_name="",  # 前回のコンテキストがない場合は空文字
            old_problem_name=""
        )

    def test_format_string(self, adapter, mock_settings_manager_with_init):
        """文字列フォーマットテスト（既存API互換性）"""
        # Arrange
        adapter.initialize("abc300", "a", "python")
        template = "Contest: {contest_name}, Problem: {problem_name}"

        # Act
        result = adapter.format_string(template)

        # Assert
        # expand_templateが呼ばれることを確認
        mock_settings_manager_with_init.expand_template.assert_called()
        assert result == "Contest: abc300, Problem: a"

    def test_format_string_not_initialized(self, adapter):
        """初期化前のformat_stringでエラーが発生することのテスト"""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Adapter not initialized"):
            adapter.format_string("test template")

    def test_to_dict(self, adapter, mock_settings_manager_with_init):
        """辞書変換テスト（既存API互換性）"""
        # Arrange
        adapter.initialize("abc300", "a", "python")

        # Act
        result = adapter.to_dict()

        # Assert
        expected_keys = {"contest_name", "problem_name", "language", "env_type",
                        "language_id", "source_file_name", "run_command"}
        assert set(result.keys()) >= expected_keys
        assert result["contest_name"] == "abc300"
        assert result["language_id"] == "4006"

    def test_to_format_dict(self, adapter, mock_settings_manager_with_init):
        """フォーマット辞書変換テスト（既存API互換性）"""
        # Arrange
        adapter.initialize("abc300", "a", "python")

        # Act
        result = adapter.to_format_dict()

        # Assert
        # to_dict()と同じ結果が返されることを確認
        assert result == adapter.to_dict()

    def test_properties(self, adapter, mock_settings_manager_with_init):
        """プロパティアクセステスト（既存API互換性）"""
        # Arrange
        adapter.initialize("abc300", "a", "python")

        # Act & Assert
        assert adapter.contest_name == "abc300"
        assert adapter.problem_name == "a"
        assert adapter.language == "python"
        assert adapter.env_type == "local"
        assert adapter.command_type == "open"
        assert adapter.old_contest_name == "abc299"
        assert adapter.old_problem_name == "b"

    def test_properties_not_initialized(self, adapter):
        """初期化前のプロパティアクセスでエラーが発生することのテスト"""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Adapter not initialized"):
            _ = adapter.contest_name

    def test_save_execution_result(self, adapter, mock_settings_manager_with_init, mock_state_manager_with_context):
        """実行結果保存テスト"""
        # Arrange
        adapter.initialize("abc300", "a", "python")

        # Act
        adapter.save_execution_result(success=True)

        # Assert
        mock_state_manager_with_context.save_execution_history.assert_called_once()
        saved_history = mock_state_manager_with_context.save_execution_history.call_args[0][0]
        assert saved_history.contest_name == "abc300"
        assert saved_history.problem_name == "a"
        assert saved_history.language == "python"
        assert saved_history.success is True
        assert saved_history.timestamp  # タイムスタンプが設定されていることを確認

    def test_save_execution_result_not_initialized(self, adapter, mock_state_manager_with_context):
        """初期化前の実行結果保存テスト"""
        # Act
        adapter.save_execution_result(success=True)

        # Assert - 初期化されていない場合は何もしない
        mock_state_manager_with_context.save_execution_history.assert_not_called()

    def test_get_execution_history(self, adapter, mock_state_manager_with_context):
        """実行履歴取得テスト"""
        # Arrange
        expected_history = [
            ExecutionHistory("abc300", "a", "python", "local", "2024-01-01T12:00:00", True)
        ]
        mock_state_manager_with_context.get_execution_history.return_value = expected_history

        # Act
        result = adapter.get_execution_history(limit=5)

        # Assert
        mock_state_manager_with_context.get_execution_history.assert_called_once_with(5)
        assert result == expected_history

    def test_to_execution_configuration_deprecated(self, adapter, mock_settings_manager_with_init):
        """非推奨のExecutionConfiguration変換テスト"""
        # Arrange
        adapter.initialize("abc300", "a", "python")

        # Act & Assert
        with pytest.raises(NotImplementedError, match="to_execution_configuration\\(\\) is deprecated"):
            adapter.to_execution_configuration()


class TestUnifiedExecutionAdapterIntegration:
    """UnifiedExecutionAdapterの統合テスト"""

    def test_full_workflow(self):
        """完全なワークフローのテスト"""
        # Arrange
        mock_settings_manager = Mock()
        mock_settings_manager.initialize = Mock()

        mock_execution_settings = Mock()
        mock_execution_settings.get_contest_name.return_value = "abc300"
        mock_execution_settings.get_problem_name.return_value = "a"
        mock_execution_settings.get_language.return_value = "python"
        mock_execution_settings.get_env_type.return_value = "local"
        mock_execution_settings.get_command_type.return_value = "open"
        mock_execution_settings.to_template_dict.return_value = {
            "contest_name": "abc300", "problem_name": "a"
        }

        mock_runtime_settings = Mock()
        mock_runtime_settings.to_runtime_dict.return_value = {
            "language_id": "4006", "source_file_name": "main.py"
        }

        mock_settings_manager.get_execution_settings.return_value = mock_execution_settings
        mock_settings_manager.get_runtime_settings.return_value = mock_runtime_settings
        mock_settings_manager.expand_template.side_effect = lambda template, context: template.format(**context)

        mock_state_manager = Mock()
        mock_state_manager.load_session_context.return_value = None
        mock_state_manager.save_session_context = Mock()
        mock_state_manager.save_execution_history = Mock()

        adapter = UnifiedExecutionAdapter(mock_settings_manager, mock_state_manager)

        # Act
        adapter.initialize("abc300", "a", "python")
        formatted = adapter.format_string("Problem: {problem_name}")
        context_dict = adapter.to_dict()
        adapter.save_execution_result(True)

        # Assert
        assert formatted == "Problem: a"
        assert "contest_name" in context_dict
        assert "language_id" in context_dict
        mock_state_manager.save_execution_history.assert_called_once()
