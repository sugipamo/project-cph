from src.env.step.run_step_base import RunStep
from src.env.step.run_step_registry import register_run_step_type

@register_run_step_type("rmtree")
class RmtreeRunStep(RunStep):
    """
    ディレクトリ削除用のRunStep。
    cmd[0]=削除対象ディレクトリパス
    """
    def validate(self) -> bool:
        if not self.cmd or len(self.cmd) < 1:
            raise ValueError("RmtreeRunStep: cmdには削除対象ディレクトリパスが1つ以上必要です")
        return True
    @property
    def target(self) -> str:
        """削除対象ディレクトリパス"""
        return self.cmd[0] 