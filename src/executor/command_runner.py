from typing import List
from src.context.user_input_parser import UserInputParser
from src.env.env_workflow_service import EnvWorkflowService

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
        # パーサーの初期化
        context = UserInputParser().from_args(args)
        # コマンドタイプに対応するrun_steps_dict_listをenv.jsonから取得
        try:
            run_steps_dict_list = context.env_json[context.language]["commands"][context.command_type]["steps"]
        except Exception as e:
            raise ValueError(f"env.jsonからコマンド({context.command_type})のsteps取得に失敗: {e}")
        service = EnvWorkflowService.from_context(context)
        result = service.run_workflow(run_steps_dict_list)
        print(result)