from typing import List
from src.context.user_input_parser import UserInputParser
from src.env.env_workflow_service import EnvWorkflowService
import os

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
        # workspace_pathの決定
        workspace_path = None
        if "--workspace" in args:
            idx = args.index("--workspace")
            if idx + 1 < len(args):
                workspace_path = args[idx + 1]
        if not workspace_path:
            lang_conf = context.env_json.get(context.language, {})
            workspace_path = lang_conf.get("workspace_path")
        if not workspace_path:
            workspace_path = os.getcwd()
        service = EnvWorkflowService.from_context(context, workspace_path=workspace_path)
        result = service.run_workflow(run_steps_dict_list)
        print(result)