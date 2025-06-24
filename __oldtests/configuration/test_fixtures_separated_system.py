"""分離システム用テストフィクスチャ

runtime分離テスト用の共通フィクスチャとモック
"""
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock

import pytest

# Infrastructure層に移動されたインターフェースをインポート
from src.infrastructure.persistence.state import ExecutionHistory, IStateRepository, SessionContext

# 互換性のためのエイリアス
IStateManager = IStateRepository


class MockExecutionSettings:
    """テスト用ExecutionSettings実装"""

    def __init__(self, contest_name: str = "abc300", problem_name: str = "a",
                 language: str = "python", env_type: str = "local",
                 command_type: str = "open"):
        self._contest_name = contest_name
        self._problem_name = problem_name
        self._language = language
        self._env_type = env_type
        self._command_type = command_type
        self._old_contest_name = "abc299"
        self._old_problem_name = "b"
        self._paths = {
            "contest_current_path": "./contest_current",
            "contest_stock_path": f"./contest_stock/{language}/{contest_name}/{problem_name}",
            "contest_template_path": "./contest_template",
            "workspace_path": "./workspace"
        }
        self._file_patterns = {
            "contest_files": ["*.py"],
            "test_files": ["*.txt", "*.in", "*.out"]
        }

    def get_contest_name(self) -> str:
        return self._contest_name

    def get_problem_name(self) -> str:
        return self._problem_name

    def get_language(self) -> str:
        return self._language

    def get_env_type(self) -> str:
        return self._env_type

    def get_command_type(self) -> str:
        return self._command_type

    def get_old_contest_name(self) -> str:
        return self._old_contest_name

    def get_old_problem_name(self) -> str:
        return self._old_problem_name

    def get_paths(self) -> Dict[str, str]:
        return self._paths.copy()

    def get_file_patterns(self) -> Dict[str, List[str]]:
        return self._file_patterns.copy()

    def to_template_dict(self) -> Dict[str, str]:
        return {
            "contest_name": self._contest_name,
            "problem_name": self._problem_name,
            "old_contest_name": self._old_contest_name,
            "old_problem_name": self._old_problem_name,
            "language": self._language,
            "language_name": self._language,
            "env_type": self._env_type,
            "command_type": self._command_type,
            **self._paths
        }


class MockRuntimeSettings:
    """テスト用RuntimeSettings実装"""

    def __init__(self, language: str = "python"):
        self._language_configs = {
            "python": {
                "language_id": "4006",
                "source_file_name": "main.py",
                "run_command": "python3",
                "timeout_seconds": 300,
                "retry_settings": {"max_attempts": 3}
            },
            "cpp": {
                "language_id": "4003",
                "source_file_name": "main.cpp",
                "run_command": "g++ -o main main.cpp && ./main",
                "timeout_seconds": 300,
                "retry_settings": {"max_attempts": 3}
            }
        }
        self._config = self._language_configs.get(language, self._language_configs["python"])

    def get_language_id(self) -> str:
        return self._config["language_id"]

    def get_source_file_name(self) -> str:
        return self._config["source_file_name"]

    def get_run_command(self) -> str:
        return self._config["run_command"]

    def get_timeout_seconds(self) -> int:
        return self._config["timeout_seconds"]

    def get_retry_settings(self) -> Dict[str, Any]:
        return self._config["retry_settings"].copy()

    def to_runtime_dict(self) -> Dict[str, str]:
        return {
            "language_id": self._config["language_id"],
            "source_file_name": self._config["source_file_name"],
            "run_command": self._config["run_command"],
            "timeout_seconds": str(self._config["timeout_seconds"])
        }


class MockStateManager(IStateManager):
    """テスト用StateManager実装"""

    def __init__(self):
        self._execution_history: List[ExecutionHistory] = []
        self._session_context: SessionContext = None
        self._user_specified_values: Dict[str, Any] = {}

    def save_execution_history(self, history: ExecutionHistory) -> None:
        self._execution_history.append(history)

    def get_execution_history(self, limit: int = 10) -> List[ExecutionHistory]:
        return self._execution_history[-limit:]

    def save_session_context(self, context: SessionContext) -> None:
        self._session_context = context

    def load_session_context(self) -> SessionContext:
        return self._session_context

    def save_user_specified_values(self, values: Dict[str, Any]) -> None:
        self._user_specified_values.update(values)

    def get_user_specified_values(self) -> Dict[str, Any]:
        return self._user_specified_values.copy()

    def clear_session(self) -> None:
        self._session_context = None
        self._user_specified_values.clear()


class MockSettingsManager:
    """テスト用SettingsManager実装"""

    def __init__(self):
        self._execution_settings = MockExecutionSettings()
        self._runtime_settings_cache = {}

    def get_execution_settings(self):
        return self._execution_settings

    def get_runtime_settings(self, language: str):
        if language not in self._runtime_settings_cache:
            self._runtime_settings_cache[language] = MockRuntimeSettings(language)
        return self._runtime_settings_cache[language]

    def save_execution_context(self, context: Dict[str, Any]) -> None:
        # Mock implementation - no actual saving
        pass

    def load_execution_context(self) -> Dict[str, Any]:
        # Mock implementation - return empty context
        return {}

    def expand_template(self, template: str, context: Dict[str, str]) -> str:
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


# pytest フィクスチャ

@pytest.fixture
def mock_execution_settings():
    """ExecutionSettings のモックフィクスチャ"""
    return MockExecutionSettings()


@pytest.fixture
def mock_runtime_settings():
    """RuntimeSettings のモックフィクスチャ"""
    return MockRuntimeSettings()


@pytest.fixture
def mock_state_manager():
    """StateManager のモックフィクスチャ"""
    return MockStateManager()


@pytest.fixture
def mock_settings_manager():
    """SettingsManager のモックフィクスチャ"""
    return MockSettingsManager()


@pytest.fixture
def sample_execution_history():
    """サンプル実行履歴のフィクスチャ"""
    return ExecutionHistory(
        contest_name="abc300",
        problem_name="a",
        language="python",
        env_type="local",
        timestamp="2024-01-01T12:00:00",
        success=True
    )


@pytest.fixture
def sample_session_context():
    """サンプルセッションコンテキストのフィクスチャ"""
    return SessionContext(
        current_contest="abc300",
        current_problem="a",
        current_language="python",
        previous_contest="abc299",
        previous_problem="b",
        user_specified_fields={"contest_name": True, "problem_name": True}
    )


@pytest.fixture
def sample_template_context():
    """サンプルテンプレートコンテキストのフィクスチャ"""
    return {
        "contest_name": "abc300",
        "problem_name": "a",
        "language": "python",
        "language_name": "python",
        "env_type": "local",
        "command_type": "open",
        "contest_current_path": "./contest_current",
        "contest_stock_path": "./contest_stock/python/abc300/a",
        "language_id": "4006",
        "source_file_name": "main.py",
        "run_command": "python3"
    }
