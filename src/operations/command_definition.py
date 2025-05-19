from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CommandDefinition:
    """
    コマンドの定義を保持するクラス
    """
    name: str
    description: str
    run: List[Any]  # 実行するコマンドのリスト
    options: Dict[str, Any] = None  # コマンドのオプション 