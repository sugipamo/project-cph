"""
Execution data holder
"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ExecutionData:
    """
    純粋な実行データを保持するクラス
    バリデーションや設定解決などの責務は持たない
    """
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: dict
    resolver: Optional[object] = None  # ConfigResolver型（循環import回避のためobject型で）
    dockerfile: Optional[str] = None
    oj_dockerfile: Optional[str] = None
    old_execution_context: Optional['ExecutionData'] = None