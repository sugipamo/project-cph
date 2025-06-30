"""セッションコンテキストのデータモデル"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class SessionContext:
    """セッションコンテキスト"""
    current_contest: str
    current_problem: str
    current_language: str
    previous_contest: str
    previous_problem: str
    user_specified_fields: Dict[str, bool]  # どのフィールドがユーザー指定か
