from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class RunStep:
    """
    1つの実行ステップ（コマンドや操作）を表す基底クラス。
    type, cmd, 各種フラグを持つ。
    """
    type: str
    cmd: List[str] = field(default_factory=list)
    force_env_type: Optional[str] = None
    allow_failure: bool = False
    show_output: bool = True

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RunStep":
        return cls(
            type=d["type"],
            cmd=d.get("cmd", []),
            force_env_type=d.get("force_env_type"),
            allow_failure=d.get("allow_failure"),
            show_output=d.get("show_output")
        )

    def validate(self) -> bool:
        return True 