from typing import List
from src.context.user_input_parser import UserInputParser
from src.env.env_workflow_service import EnvWorkflowService
from src.env.build_di_container_and_context import build_di_container_and_context

class CommandRunner:
    """
    コマンドライン引数からコマンドを実行するクラス
    """
    def __init__(self, user_input_parser=None, di_builder=None, workflow_service_cls=None):
        self.user_input_parser = user_input_parser or UserInputParser()
        self.di_builder = di_builder or build_di_container_and_context
        self.workflow_service_cls = workflow_service_cls or EnvWorkflowService

    @classmethod
    def from_args(cls):
        """
        本番用の依存解決でCommandRunnerを生成
        """
        return cls()

    def run(self, args: List[str]) -> None:
        """
        コマンドを実行する
        Args:
            args: コマンドライン引数
        Raises:
            ValueError: パースに失敗した場合
        """
        context = self.user_input_parser.from_args(args)
        context, di_container = self.di_builder(context)
        service = self.workflow_service_cls.from_context(context, di_container)
        result = service.run_workflow()
        print(result)