"""Sys provider - sysモジュールの副作用を集約するプロバイダー"""
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional


class SysProvider(ABC):
    """sysモジュールの副作用を集約する抽象プロバイダー"""

    @abstractmethod
    def get_argv(self) -> List[str]:
        """コマンドライン引数を取得"""
        pass

    @abstractmethod
    def exit(self, code: int = 0) -> None:
        """プログラムを終了"""
        pass

    @abstractmethod
    def get_platform(self) -> str:
        """プラットフォーム情報を取得"""
        pass

    @abstractmethod
    def get_version_info(self) -> Any:
        """Pythonバージョン情報を取得"""
        pass


class SystemSysProvider(SysProvider):
    """実際のsysモジュールを使用するプロバイダー"""

    def get_argv(self) -> List[str]:
        """コマンドライン引数を取得"""
        return sys.argv

    def exit(self, code: int = 0) -> None:
        """プログラムを終了"""
        sys.exit(code)

    def get_platform(self) -> str:
        """プラットフォーム情報を取得"""
        return sys.platform

    def get_version_info(self) -> Any:
        """Pythonバージョン情報を取得"""
        return sys.version_info


class MockSysProvider(SysProvider):
    """テスト用のモックsysプロバイダー"""

    def __init__(self, argv: Optional[List[str]] = None, platform: str = "test"):
        # フォールバック処理は禁止、必要なエラーを見逃すことになる
        if argv is None:
            raise ValueError("argv parameter is required")
        self._argv = argv
        self._platform = platform
        self._exit_code: Optional[int] = None
        self._exit_callback: Optional[Callable[[int], None]] = None

    def get_argv(self) -> List[str]:
        """コマンドライン引数を取得"""
        return self._argv

    def exit(self, code: int = 0) -> None:
        """プログラムを終了（モック）"""
        self._exit_code = code
        if self._exit_callback:
            self._exit_callback(code)

    def get_platform(self) -> str:
        """プラットフォーム情報を取得"""
        return self._platform

    def get_version_info(self) -> Any:
        """Pythonバージョン情報を取得"""
        return sys.version_info  # これは実際の値を返す

    def set_argv(self, argv: List[str]) -> None:
        """テスト用：コマンドライン引数を設定"""
        self._argv = argv

    def set_exit_callback(self, callback: Callable[[int], None]) -> None:
        """テスト用：exit時のコールバックを設定"""
        self._exit_callback = callback

    def get_last_exit_code(self) -> Optional[int]:
        """テスト用：最後のexit codeを取得"""
        return self._exit_code
