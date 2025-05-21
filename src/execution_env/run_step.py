from dataclasses import dataclass, field
from typing import List, Dict, Any, Type
from src.execution_env.run_step_base import RunStep
from src.execution_env.run_steps import RunSteps
from src.execution_env.run_step_shell import ShellRunStep
from src.execution_env.run_step_copy import CopyRunStep
from src.execution_env.run_step_oj import OjRunStep
from src.execution_env.run_step_registry import register_run_step_type, RUN_STEP_TYPE_MAP

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
        """
        dictからtypeに応じたRunStepサブクラスを生成し、バリデーションも行う。
        """
        type_ = d["type"]
        cmd_ = d.get("cmd", [])
        extra = {k: v for k, v in d.items() if k not in ("type", "cmd")}
        step = cls(type=type_, cmd=cmd_, extra=extra)
        step.validate()
        return step

    def validate(self) -> bool:
        """
        サブクラスで必須フィールドや値のチェックを実装。
        基底クラスは常にTrueを返す。
        """
        return True

# type→クラスのマッピング辞書
RUN_STEP_TYPE_MAP: Dict[str, Type[RunStep]] = {}

def register_run_step_type(type_name: str):
    """
    RunStepサブクラスをtype名で登録するデコレータ。
    """
    def decorator(cls):
        RUN_STEP_TYPE_MAP[type_name] = cls
        return cls
    return decorator

class RunSteps:
    """
    複数のRunStepを管理するクラス。
    from_listでdictリストから生成、filterやバリデーションも提供。
    """
    def __init__(self, steps: List[RunStep]):
        self.steps = steps

    @classmethod
    def from_list(cls, lst: List[Dict[str, Any]]) -> "RunSteps":
        """
        dictリストからRunStepサブクラスのリストを生成し、RunStepsとして返す。
        """
        return cls([RunStep.from_dict(d) for d in lst])

    def __iter__(self):
        return iter(self.steps)

    def __getitem__(self, idx):
        return self.steps[idx]

    def __len__(self):
        return len(self.steps)

    def validate_all(self) -> None:
        """
        全stepのバリデーションを一括で実行。
        """
        for step in self.steps:
            if hasattr(step, "validate"):
                step.validate()

@register_run_step_type("shell")
class ShellRunStep(RunStep):
    """
    shellコマンド実行用のRunStep。
    """
    def validate(self) -> bool:
        if not self.cmd or not isinstance(self.cmd, list):
            raise ValueError("ShellRunStep: cmdは必須でリストである必要があります")
        return True

@register_run_step_type("copy")
class CopyRunStep(RunStep):
    """
    ファイルコピー用のRunStep。
    cmd[0]=src, cmd[1]=dst
    """
    def validate(self) -> bool:
        if not self.cmd or len(self.cmd) < 2:
            raise ValueError("CopyRunStep: cmdにはsrcとdstの2つが必要です")
        return True
    @property
    def src(self) -> str:
        """コピー元パス"""
        return self.cmd[0]
    @property
    def dst(self) -> str:
        """コピー先パス"""
        return self.cmd[1]

@register_run_step_type("oj")
class OjRunStep(RunStep):
    """
    ojコマンド用のRunStep。
    """
    def validate(self) -> bool:
        if not self.cmd or not isinstance(self.cmd, list):
            raise ValueError("OjRunStep: cmdは必須でリストである必要があります")
        # 追加のoj専用バリデーションがあればここに
        return True

register_run_step_type("shell")(ShellRunStep)
register_run_step_type("copy")(CopyRunStep)
register_run_step_type("oj")(OjRunStep)