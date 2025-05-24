from src.env.step.run_step_base import RunStep
from src.env.step.run_step_registry import register_run_step_type

@register_run_step_type("movetree")
class MoveTreeRunStep(RunStep):
    """
    ディレクトリ移動用のRunStep。
    cmd[0]=移動元ディレクトリ, cmd[1]=移動先ディレクトリ
    """
    def validate(self) -> bool:
        if not self.cmd or len(self.cmd) < 2:
            raise ValueError("MoveTreeRunStep: cmdにはsrcとdstの2つが必要です")
        return True
    @property
    def src(self) -> str:
        return self.cmd[0]
    @property
    def dst(self) -> str:
        return self.cmd[1] 