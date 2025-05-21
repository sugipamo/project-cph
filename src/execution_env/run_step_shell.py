from src.execution_env.run_step_base import RunStep

class ShellRunStep(RunStep):
    """
    shellコマンド実行用のRunStep。
    """
    def validate(self) -> bool:
        if not self.cmd or not isinstance(self.cmd, list):
            raise ValueError("ShellRunStep: cmdは必須でリストである必要があります")
        return True 