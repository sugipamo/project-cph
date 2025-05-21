from src.env.step.run_step_base import RunStep
from src.env.step.run_step_registry import register_run_step_type

@register_run_step_type("remove")
class RemoveRunStep(RunStep):
    """
    ファイル・ディレクトリ削除用のRunStep。
    cmd[0]=削除対象パス
    """
    def validate(self) -> bool:
        if not self.cmd or len(self.cmd) < 1:
            raise ValueError("RemoveRunStep: cmdには削除対象パスが1つ以上必要です")
        return True
    @property
    def target(self) -> str:
        """削除対象パス"""
        return self.cmd[0] 