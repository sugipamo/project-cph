"""環境変数プロバイダー - 環境変数読み取りの副作用を集約"""
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EnvironmentProvider(ABC):
    """環境変数読み取りの抽象インターフェース"""

    @abstractmethod
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """環境変数を取得"""
        pass

    @abstractmethod
    def get_env_bool(self, key: str, default: bool = False) -> bool:
        """環境変数をbooleanとして取得"""
        pass

    @abstractmethod
    def get_env_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """環境変数をintegerとして取得"""
        pass

    @abstractmethod
    def get_all_env(self) -> Dict[str, str]:
        """全環境変数を取得"""
        pass


class SystemEnvironmentProvider(EnvironmentProvider):
    """システム環境変数プロバイダー - 副作用はここに集約"""

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """環境変数を取得（副作用）"""
        return os.environ.get(key, default)

    def get_env_bool(self, key: str, default: bool = False) -> bool:
        """環境変数をbooleanとして取得（副作用）"""
        value = os.environ.get(key, None)
        if value is None:
            return default
        return value.lower() in ('1', 'true', 'yes', 'on')

    def get_env_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """環境変数をintegerとして取得（副作用）"""
        value = os.environ.get(key, None)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_all_env(self) -> Dict[str, str]:
        """全環境変数を取得（副作用）"""
        return dict(os.environ)


class MockEnvironmentProvider(EnvironmentProvider):
    """テスト用モック環境変数プロバイダー - 副作用なし"""

    def __init__(self, env_vars: Optional[Dict[str, str]] = None):
        self._env_vars = env_vars or {}

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """モック環境変数取得（副作用なし）"""
        return self._env_vars.get(key, default)

    def get_env_bool(self, key: str, default: bool = False) -> bool:
        """モック環境変数boolean取得（副作用なし）"""
        value = self._env_vars.get(key, None)
        if value is None:
            return default
        return value.lower() in ('1', 'true', 'yes', 'on')

    def get_env_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """モック環境変数integer取得（副作用なし）"""
        value = self._env_vars.get(key, None)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_all_env(self) -> Dict[str, str]:
        """モック全環境変数取得（副作用なし）"""
        return self._env_vars.copy()

    def set_env(self, key: str, value: str) -> None:
        """テスト用環境変数設定"""
        self._env_vars[key] = value

    def unset_env(self, key: str) -> None:
        """テスト用環境変数削除"""
        self._env_vars.pop(key, None)

    def clear_env(self) -> None:
        """テスト用環境変数全削除"""
        self._env_vars.clear()


class WorkingDirectoryProvider(ABC):
    """カレントディレクトリ操作の抽象インターフェース"""

    @abstractmethod
    def get_cwd(self) -> str:
        """現在のワーキングディレクトリを取得"""
        pass

    @abstractmethod
    def change_cwd(self, path: str) -> None:
        """ワーキングディレクトリを変更"""
        pass


class SystemWorkingDirectoryProvider(WorkingDirectoryProvider):
    """システムワーキングディレクトリプロバイダー - 副作用はここに集約"""

    def get_cwd(self) -> str:
        """現在のワーキングディレクトリを取得（副作用）"""
        return os.getcwd()

    def change_cwd(self, path: str) -> None:
        """ワーキングディレクトリを変更（副作用）"""
        os.chdir(path)


class MockWorkingDirectoryProvider(WorkingDirectoryProvider):
    """テスト用モックワーキングディレクトリプロバイダー - 副作用なし"""

    def __init__(self, initial_cwd: str = "/mock/current/dir"):
        self._current_cwd = initial_cwd
        self._cwd_history = [initial_cwd]

    def get_cwd(self) -> str:
        """モック現在ディレクトリ取得（副作用なし）"""
        return self._current_cwd

    def change_cwd(self, path: str) -> None:
        """モックディレクトリ変更（副作用なし）"""
        self._current_cwd = path
        self._cwd_history.append(path)

    def get_cwd_history(self) -> list:
        """テスト用ディレクトリ変更履歴取得"""
        return self._cwd_history.copy()


# ユーティリティ関数（純粋関数）
def parse_debug_flag(debug_value: Optional[str]) -> bool:
    """デバッグフラグをパース（純粋関数）

    Args:
        debug_value: 環境変数の値

    Returns:
        デバッグ有効かどうか
    """
    if debug_value is None:
        return False
    return debug_value.lower() in ('1', 'true', 'yes', 'on')


def create_env_context(env_provider: EnvironmentProvider) -> Dict[str, Any]:
    """環境変数から実行コンテキストを作成（副作用をプロバイダーに委譲）

    Args:
        env_provider: 環境変数プロバイダー

    Returns:
        実行コンテキスト辞書
    """
    return {
        "debug_enabled": env_provider.get_env_bool("CPH_DEBUG_REQUEST_INFO", True),
        "log_level": env_provider.get_env("CPH_LOG_LEVEL", "INFO"),
        "timeout_seconds": env_provider.get_env_int("CPH_TIMEOUT", 300),
        "parallel_enabled": env_provider.get_env_bool("CPH_PARALLEL", True),
        "max_workers": env_provider.get_env_int("CPH_MAX_WORKERS", 4)
    }


def validate_env_context(context: Dict[str, Any]) -> Dict[str, str]:
    """環境コンテキストをバリデーション（純粋関数）

    Args:
        context: 環境コンテキスト

    Returns:
        バリデーションエラー辞書
    """
    errors = {}

    if "timeout_seconds" in context:
        timeout = context["timeout_seconds"]
        if timeout is not None and (timeout <= 0 or timeout > 3600):
            errors["timeout_seconds"] = "Timeout must be between 1 and 3600 seconds"

    if "max_workers" in context:
        workers = context["max_workers"]
        if workers is not None and (workers <= 0 or workers > 32):
            errors["max_workers"] = "Max workers must be between 1 and 32"

    if "log_level" in context:
        level = context["log_level"]
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if level not in valid_levels:
            errors["log_level"] = f"Log level must be one of: {', '.join(valid_levels)}"

    return errors
