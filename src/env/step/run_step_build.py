from src.env.step.run_step_base import RunStep
from src.env.step.run_step_registry import register_run_step_type

@register_run_step_type("build")
class BuildRunStep(RunStep):
    """
    ビルド操作用のRunStep。
    cmd: ビルドコマンドやオプション
    """
    def validate(self) -> bool:
        # cmdは空でも許容（ビルド内容が固定の場合）
        if self.cmd is not None and not isinstance(self.cmd, list):
            raise ValueError("BuildRunStep: cmdはリストである必要があります")
        return True 