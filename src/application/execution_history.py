"""実行履歴のデータモデル"""
from dataclasses import dataclass


@dataclass
class ExecutionHistory:
    """実行履歴データ"""
    contest_name: str
    problem_name: str
    language: str
    env_type: str
    timestamp: str
    success: bool
