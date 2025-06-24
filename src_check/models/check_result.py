from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class FailureLocation:
    """品質チェック失敗箇所を表すデータクラス"""
    file_path: str
    line_number: int


@dataclass(frozen=True)
class CheckResult:
    """品質チェック結果を表すデータクラス"""
    failure_locations: List[FailureLocation] = field(default_factory=list)
    fix_policy: str = ""
    fix_example_code: Optional[str] = None