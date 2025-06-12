"""実行時間計算の純粋関数 - PythonRequestから分離"""
from dataclasses import dataclass
from typing import Optional

from src.infrastructure.providers.time_provider import TimeProvider


@dataclass(frozen=True)
class ExecutionTiming:
    """実行時間情報（不変データ）"""
    start_time: float
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """実行時間を計算（純粋関数）"""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time
    
    def with_end_time(self, end_time: float) -> 'ExecutionTiming':
        """終了時刻を設定した新しいインスタンスを返却（純粋関数）"""
        return ExecutionTiming(self.start_time, end_time)


def start_timing(time_provider: TimeProvider) -> ExecutionTiming:
    """実行時間測定を開始（副作用をプロバイダーに委譲）
    
    Args:
        time_provider: 時刻プロバイダー
        
    Returns:
        開始時刻を含む実行時間情報
    """
    return ExecutionTiming(start_time=time_provider.now())


def end_timing(timing: ExecutionTiming, time_provider: TimeProvider) -> ExecutionTiming:
    """実行時間測定を終了（副作用をプロバイダーに委譲）
    
    Args:
        timing: 開始済み実行時間情報
        time_provider: 時刻プロバイダー
        
    Returns:
        終了時刻を含む実行時間情報
    """
    return timing.with_end_time(time_provider.now())


def format_execution_timing(timing: ExecutionTiming) -> str:
    """実行時間をフォーマット（純粋関数）
    
    Args:
        timing: 実行時間情報
        
    Returns:
        フォーマット済み実行時間文字列
    """
    if timing.duration is None:
        return "実行中..."
    
    duration = timing.duration
    if duration < 1.0:
        return f"{duration * 1000:.1f}ms"
    elif duration < 60.0:
        return f"{duration:.2f}s"
    else:
        minutes = int(duration // 60)
        seconds = duration % 60
        return f"{minutes}m {seconds:.1f}s"


def is_execution_timeout(timing: ExecutionTiming, timeout_seconds: float) -> bool:
    """実行タイムアウト判定（純粋関数）
    
    Args:
        timing: 実行時間情報
        timeout_seconds: タイムアウト時間（秒）
        
    Returns:
        タイムアウトしている場合True
    """
    if timing.duration is None:
        return False
    return timing.duration > timeout_seconds