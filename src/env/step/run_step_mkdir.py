from src.env.step.run_step_base import RunStep
from src.env.step.run_step_registry import register_run_step_type

@register_run_step_type("mkdir")
class MkdirRunStep(RunStep):
    """
    ディレクトリ作成用のRunStep。
    cmd[0]=作成したいディレクトリパス
    """
    def validate(self) -> bool:
        if not self.cmd or len(self.cmd) < 1:
            raise ValueError("MkdirRunStep: cmdには作成したいディレクトリパスが1つ以上必要です")
        return True
    @property
    def target(self) -> str:
        """作成対象ディレクトリパス"""
        return self.cmd[0] 