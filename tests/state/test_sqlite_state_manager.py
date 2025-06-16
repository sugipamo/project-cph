"""SqliteStateManager の単体テスト

状態管理システムの分離後のテスト
"""
import pytest
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.state.services.sqlite_state_manager import SqliteStateManager
from src.state.interfaces.state_manager import ExecutionHistory, SessionContext
from tests.configuration.test_fixtures_separated_system import (
    sample_execution_history, sample_session_context
)


class TestSqliteStateManager:
    """SqliteStateManagerの単体テスト"""
    
    @pytest.fixture
    def mock_config_repo(self):
        """SystemConfigRepositoryのモック"""
        mock_repo = Mock()
        mock_repo.save_config = Mock()
        mock_repo.get_config = Mock()
        mock_repo.get_configs_by_category = Mock()
        mock_repo.delete_config = Mock()
        return mock_repo
    
    @pytest.fixture
    def state_manager(self, mock_config_repo):
        """SqliteStateManagerのインスタンス"""
        return SqliteStateManager(mock_config_repo)
    
    def test_save_execution_history(self, state_manager, mock_config_repo, sample_execution_history):
        """実行履歴の保存テスト"""
        # Act
        state_manager.save_execution_history(sample_execution_history)
        
        # Assert
        mock_config_repo.save_config.assert_called_once()
        call_args = mock_config_repo.save_config.call_args
        
        assert call_args.kwargs["category"] == "execution_history"
        assert "history_" in call_args.kwargs["key"]
        
        # 保存されたデータの検証
        saved_data = json.loads(call_args.kwargs["value"])
        assert saved_data["contest_name"] == "abc300"
        assert saved_data["problem_name"] == "a"
        assert saved_data["language"] == "python"
        assert saved_data["success"] is True
    
    def test_get_execution_history(self, state_manager, mock_config_repo):
        """実行履歴の取得テスト"""
        # Arrange
        mock_config = Mock()
        mock_config.key = "history_2024-01-01T12:00:00"
        mock_config.value = json.dumps({
            "contest_name": "abc300",
            "problem_name": "a",
            "language": "python",
            "env_type": "local",
            "timestamp": "2024-01-01T12:00:00",
            "success": True
        })
        mock_config_repo.get_configs_by_category.return_value = [mock_config]
        
        # Act
        result = state_manager.get_execution_history(limit=5)
        
        # Assert
        assert len(result) == 1
        history = result[0]
        assert history.contest_name == "abc300"
        assert history.problem_name == "a"
        assert history.language == "python"
        assert history.success is True
        mock_config_repo.get_configs_by_category.assert_called_with("execution_history")
    
    def test_get_execution_history_invalid_data(self, state_manager, mock_config_repo):
        """無効なデータがある場合の実行履歴取得テスト"""
        # Arrange
        mock_config_valid = Mock()
        mock_config_valid.key = "history_valid"
        mock_config_valid.value = json.dumps({
            "contest_name": "abc300",
            "problem_name": "a",
            "language": "python",
            "env_type": "local",
            "timestamp": "2024-01-01T12:00:00",
            "success": True
        })
        
        mock_config_invalid = Mock()
        mock_config_invalid.key = "history_invalid"
        mock_config_invalid.value = "invalid json"
        
        mock_config_repo.get_configs_by_category.return_value = [
            mock_config_valid, mock_config_invalid
        ]
        
        # Act
        result = state_manager.get_execution_history()
        
        # Assert - 有効なデータのみが返される
        assert len(result) == 1
        assert result[0].contest_name == "abc300"
    
    def test_save_session_context(self, state_manager, mock_config_repo, sample_session_context):
        """セッションコンテキストの保存テスト"""
        # Act
        state_manager.save_session_context(sample_session_context)
        
        # Assert
        mock_config_repo.save_config.assert_called_once()
        call_args = mock_config_repo.save_config.call_args
        
        assert call_args.kwargs["key"] == "current_session"
        assert call_args.kwargs["category"] == "session_state"
        
        # 保存されたデータの検証
        saved_data = json.loads(call_args.kwargs["value"])
        assert saved_data["current_contest"] == "abc300"
        assert saved_data["current_problem"] == "a"
        assert saved_data["previous_contest"] == "abc299"
    
    def test_load_session_context(self, state_manager, mock_config_repo):
        """セッションコンテキストの読み込みテスト"""
        # Arrange
        mock_config = Mock()
        mock_config.value = json.dumps({
            "current_contest": "abc300",
            "current_problem": "a",
            "current_language": "python",
            "previous_contest": "abc299",
            "previous_problem": "b",
            "user_specified_fields": {"contest_name": True}
        })
        mock_config_repo.get_config.return_value = mock_config
        
        # Act
        result = state_manager.load_session_context()
        
        # Assert
        assert result is not None
        assert result.current_contest == "abc300"
        assert result.current_problem == "a"
        assert result.previous_contest == "abc299"
        assert result.user_specified_fields == {"contest_name": True}
        mock_config_repo.get_config.assert_called_with("current_session")
    
    def test_load_session_context_no_data(self, state_manager, mock_config_repo):
        """データが存在しない場合のセッションコンテキスト読み込みテスト"""
        # Arrange
        mock_config_repo.get_config.return_value = None
        
        # Act
        result = state_manager.load_session_context()
        
        # Assert
        assert result is None
    
    def test_save_user_specified_values(self, state_manager, mock_config_repo):
        """ユーザー指定値の保存テスト"""
        # Arrange
        values = {"contest_name": "abc300", "language": "python"}
        
        # Act
        state_manager.save_user_specified_values(values)
        
        # Assert
        mock_config_repo.save_config.assert_called_once()
        call_args = mock_config_repo.save_config.call_args
        
        assert call_args.kwargs["key"] == "user_values"
        assert call_args.kwargs["category"] == "user_specified"
        
        saved_data = json.loads(call_args.kwargs["value"])
        assert saved_data == values
    
    def test_get_user_specified_values(self, state_manager, mock_config_repo):
        """ユーザー指定値の取得テスト"""
        # Arrange
        expected_values = {"contest_name": "abc300", "language": "python"}
        mock_config = Mock()
        mock_config.value = json.dumps(expected_values)
        mock_config_repo.get_config.return_value = mock_config
        
        # Act
        result = state_manager.get_user_specified_values()
        
        # Assert
        assert result == expected_values
        mock_config_repo.get_config.assert_called_with("user_values")
    
    def test_get_user_specified_values_no_data(self, state_manager, mock_config_repo):
        """データが存在しない場合のユーザー指定値取得テスト"""
        # Arrange
        mock_config_repo.get_config.return_value = None
        
        # Act
        result = state_manager.get_user_specified_values()
        
        # Assert
        assert result == {}
    
    def test_clear_session(self, state_manager, mock_config_repo):
        """セッション情報のクリアテスト"""
        # Arrange
        mock_config = Mock()
        mock_config.key = "current_session"
        mock_config_repo.get_configs_by_category.return_value = [mock_config]
        
        # Act
        state_manager.clear_session()
        
        # Assert
        mock_config_repo.get_configs_by_category.assert_called_with("session_state")
        mock_config_repo.delete_config.assert_called_with("current_session")


class TestExecutionHistory:
    """ExecutionHistoryデータクラスのテスト"""
    
    def test_execution_history_creation(self):
        """ExecutionHistoryの作成テスト"""
        # Act
        history = ExecutionHistory(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            timestamp="2024-01-01T12:00:00",
            success=True
        )
        
        # Assert
        assert history.contest_name == "abc300"
        assert history.problem_name == "a"
        assert history.language == "python"
        assert history.env_type == "local"
        assert history.timestamp == "2024-01-01T12:00:00"
        assert history.success is True


class TestSessionContext:
    """SessionContextデータクラスのテスト"""
    
    def test_session_context_creation(self):
        """SessionContextの作成テスト"""
        # Act
        context = SessionContext(
            current_contest="abc300",
            current_problem="a",
            current_language="python",
            previous_contest="abc299",
            previous_problem="b",
            user_specified_fields={"contest_name": True}
        )
        
        # Assert
        assert context.current_contest == "abc300"
        assert context.current_problem == "a"
        assert context.current_language == "python"
        assert context.previous_contest == "abc299"
        assert context.previous_problem == "b"
        assert context.user_specified_fields == {"contest_name": True}