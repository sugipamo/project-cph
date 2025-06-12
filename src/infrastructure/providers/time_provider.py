"""時刻プロバイダー - 時刻取得の副作用を集約"""
import time
from abc import ABC, abstractmethod
from typing import Optional


class TimeProvider(ABC):
    """時刻取得の抽象インターフェース"""

    @abstractmethod
    def now(self) -> float:
        """現在時刻をUnixタイムスタンプで取得"""
        pass

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """指定秒数待機"""
        pass


class SystemTimeProvider(TimeProvider):
    """システム時刻プロバイダー - 副作用はここに集約"""

    def now(self) -> float:
        """現在時刻をUnixタイムスタンプで取得（副作用）"""
        return time.time()

    def sleep(self, seconds: float) -> None:
        """指定秒数待機（副作用）"""
        time.sleep(seconds)


class MockTimeProvider(TimeProvider):
    """テスト用モック時刻プロバイダー - 副作用なし"""

    def __init__(self, initial_time: float = 0.0):
        self._current_time = initial_time
        self._sleep_calls = []

    def now(self) -> float:
        """モック現在時刻取得（副作用なし）"""
        return self._current_time

    def sleep(self, seconds: float) -> None:
        """モック待機（副作用なし）"""
        self._sleep_calls.append(seconds)
        self._current_time += seconds

    def advance_time(self, seconds: float) -> None:
        """テスト用時刻進行"""
        self._current_time += seconds

    def set_time(self, timestamp: float) -> None:
        """テスト用時刻設定"""
        self._current_time = timestamp

    def get_sleep_calls(self) -> list:
        """テスト用スリープ呼び出し履歴取得"""
        return self._sleep_calls.copy()


class FixedTimeProvider(TimeProvider):
    """固定時刻プロバイダー - 決定的テスト用"""

    def __init__(self, fixed_time: float):
        self._fixed_time = fixed_time

    def now(self) -> float:
        """固定時刻を返却（副作用なし）"""
        return self._fixed_time

    def sleep(self, seconds: float) -> None:
        """何もしない（副作用なし）"""
        pass


# ユーティリティ関数（純粋関数）
def calculate_duration(start_time: float, end_time: float) -> float:
    """実行時間を計算（純粋関数）
    
    Args:
        start_time: 開始時刻
        end_time: 終了時刻
        
    Returns:
        実行時間（秒）
    """
    return end_time - start_time


def format_duration(duration: float) -> str:
    """実行時間を人間可読形式にフォーマット（純粋関数）
    
    Args:
        duration: 実行時間（秒）
        
    Returns:
        フォーマットされた時間文字列
    """
    if duration < 1.0:
        return f"{duration * 1000:.1f}ms"
    elif duration < 60.0:
        return f"{duration:.2f}s"
    else:
        minutes = int(duration // 60)
        seconds = duration % 60
        return f"{minutes}m {seconds:.1f}s"


def is_timeout_exceeded(start_time: float, current_time: float, timeout_seconds: float) -> bool:
    """タイムアウト判定（純粋関数）
    
    Args:
        start_time: 開始時刻
        current_time: 現在時刻  
        timeout_seconds: タイムアウト時間（秒）
        
    Returns:
        タイムアウトしている場合True
    """
    return (current_time - start_time) > timeout_seconds