from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class RunStep:
    """
    1つの実行ステップ（コマンドや操作）を表す基底クラス。
    type, cmd, extra情報を持つ。
    """
    type: str
    cmd: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RunStep":
        type_ = d["type"]
        cmd_ = d["cmd"] if "cmd" in d else []
        extra = {k: v for k, v in d.items() if k not in ("type", "cmd")}
        step = cls(type=type_, cmd=cmd_, extra=extra)
        step.validate()
        return step

    def validate(self) -> bool:
        return True 