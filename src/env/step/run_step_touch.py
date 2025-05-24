from src.env.step.run_step_base import RunStep
from src.env.step.run_step_registry import register_run_step_type

@register_run_step_type("touch")
class TouchRunStep(RunStep):
    """
    ファイル作成用のRunStep。
    cmd[0]=作成したいファイルパス
    """
    def validate(self) -> bool:
        if not self.cmd or len(self.cmd) < 1:
            raise ValueError("TouchRunStep: cmdには作成したいファイルパスが1つ以上必要です")
        return True
    @property
    def target(self) -> str:
        """作成対象ファイルパス"""
        return self.cmd[0] 