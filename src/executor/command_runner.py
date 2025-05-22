from typing import List
from src.context.user_input_parser import UserInputParser
from src.env.env_workflow_service import EnvWorkflowService
from src.operations.di_container import DIContainer

def setup_di_container():
    # driver登録責務は下位レイヤに移譲
    return DIContainer()

class CommandRunner:
    """
    コマンドライン引数からコマンドを実行するクラス
    """
    @classmethod
    def run(cls, args: List[str]) -> None:
        """
        コマンドを実行する
        
        Args:
            args: コマンドライン引数
            
        Raises:
            ValueError: パースに失敗した場合
        """
        context = UserInputParser().from_args(args)
        try:
            steps = context.env_json[context.language]["commands"][context.command_type]["steps"]
        except Exception as e:
            raise ValueError(f"env.jsonからコマンド({context.command_type})のsteps取得に失敗: {e}")

        di = setup_di_container()
        service = EnvWorkflowService.from_context(context, di_container=di)
        result = service.run_workflow(steps)
        print(result)