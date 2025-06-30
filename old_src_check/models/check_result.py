from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class LogLevel(Enum):
    """ログレベル（数値が大きいほど重要）"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass(frozen=True)
class FailureLocation:
    """品質チェック失敗箇所を表すデータクラス"""
    file_path: str
    line_number: int


@dataclass(frozen=True)
class CheckResult:
    """品質チェック結果を表すデータクラス
    
    Note: log_levelは必須パラメータです。
    既存のコードはこの変更により動作しなくなります。
    """
    title: str
    log_level: LogLevel  # 必須パラメータとして先頭に配置
    failure_locations: List[FailureLocation] = field(default_factory=list)
    fix_policy: str = ""
    fix_example_code: Optional[str] = None