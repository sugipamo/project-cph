from src.execution_env.run_step_base import RunStep
from src.execution_env.run_step_registry import register_run_step_type

@register_run_step_type("shell")
class ShellRunStep(RunStep):
    """
    shellコマンド実行用のRunStep。
    """
    def validate(self) -> bool:
        if not self.cmd or not isinstance(self.cmd, list):
            raise ValueError("ShellRunStep: cmdは必須でリストである必要があります")
        return True 