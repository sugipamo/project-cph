from typing import List
from src.context.user_input_parser import UserInputParser
from src.env.env_workflow_service import EnvWorkflowService

def resolve_driver(context):
    env_type = getattr(context, 'env_type', 'local').lower()
    if env_type == 'local':
        from src.operations.shell.local_shell_driver import LocalShellDriver
        return LocalShellDriver()
    # 今後docker等もここで分岐
    return None

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

        driver = resolve_driver(context)
        service = EnvWorkflowService.from_context(context, workspace_path=context.workspace_path)
        result = service.run_workflow(steps, driver=driver)
        print(result)