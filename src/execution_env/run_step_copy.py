from src.execution_env.run_step_base import RunStep
from src.execution_env.run_step_registry import register_run_step_type

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