from src.execution_env.run_step.run_step_base import RunStep
from src.execution_env.run_step.run_step_registry import register_run_step_type

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