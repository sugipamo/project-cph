from typing import List
from src.context.user_input_parser import UserInputParser
from src.env.env_workflow_service import EnvWorkflowService
from src.env.env_context_with_di import build_di_container_and_context

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
        context, di_container = build_di_container_and_context(context)
        service = EnvWorkflowService.from_context(context, di_container)
        result = service.run_workflow()
        print(result)