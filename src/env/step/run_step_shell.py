from src.env.step.run_step_base import RunStep
from src.env.step.run_step_registry import register_run_step_type

@register_run_step_type("shell")
class ShellRunStep(RunStep):
    """
    shellコマンド実行用のRunStep。
    """
    @classmethod
    def from_dict(cls, d):
        return cls(
            type=d["type"],
            cmd=d.get("cmd", []),
            force_env_type=d.get("force_env_type"),
            allow_failure=d.get("allow_failure"),
            show_output=d.get("show_output"),
            cwd=d.get("cwd")
        )
    def validate(self) -> bool:
        if not self.cmd or not isinstance(self.cmd, list):
            raise ValueError("ShellRunStep: cmdは必須でリストである必要があります")
        return True 