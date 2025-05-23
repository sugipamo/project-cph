from typing import List
from src.context.user_input_parser import UserInputParser
from src.env.env_workflow_service import EnvWorkflowService
from src.env.build_di_container_and_context import build_di_container_and_context

class CommandRunner:
    """
    コマンドライン引数からコマンドを実行するクラス
    """
    def __init__(self, user_input_parser, di_builder, workflow_service_cls):
        self.user_input_parser = user_input_parser
        self.di_builder = di_builder
        self.workflow_service_cls = workflow_service_cls

    @classmethod
    def from_args(cls, user_input_parser=None, di_builder=None, workflow_service_cls=None):
        """
        本番用の依存解決でCommandRunnerを生成
        """
        if user_input_parser is None:
            from src.context.user_input_parser import LocalSystemInfoProvider
            user_input_parser = UserInputParser(LocalSystemInfoProvider(), UserInputParser._default_dockerfile_loader)
        if di_builder is None:
            di_builder = build_di_container_and_context
        if workflow_service_cls is None:
            workflow_service_cls = EnvWorkflowService
        return cls(user_input_parser, di_builder, workflow_service_cls)

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