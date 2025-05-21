from src.execution_env.run_step_base import RunStep

class OjRunStep(RunStep):
    """
    ojコマンド用のRunStep。
    """
    def validate(self) -> bool:
        if not self.cmd or not isinstance(self.cmd, list):
            raise ValueError("OjRunStep: cmdは必須でリストである必要があります")
        # 追加のoj専用バリデーションがあればここに
        return True 